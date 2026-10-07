import { useCallback, useEffect, useRef, useState } from "react";
import { api, consultaStream } from "./api";
import type { EventoConsulta, Mensaje, Valoracion } from "./types";

export interface OpcionesChat {
  k: number;
  manual: string | null; // null = detección automática del manual
}

const nuevoId = () => crypto.randomUUID();
const CLAVE_CONVERSACION = "asistente:conversacion";

function obtenerConversacionId() {
  try {
    const guardado = window.localStorage.getItem(CLAVE_CONVERSACION);
    if (guardado) return guardado;
    const id = nuevoId();
    window.localStorage.setItem(CLAVE_CONVERSACION, id);
    return id;
  } catch {
    return nuevoId();
  }
}

/** Aplica un evento del stream al mensaje del asistente que se está construyendo. */
function aplicarEvento(m: Mensaje, ev: EventoConsulta): Mensaje {
  switch (ev.tipo) {
    case "plan":
      return { ...m, plan: { consulta: ev.consulta, manual: ev.manual, origen: ev.origen } };
    case "memoria":
      return { ...m, recuerdos: ev.recuerdos };
    case "fuentes":
      return { ...m, fuentes: ev.fuentes };
    case "token":
      return { ...m, content: m.content + ev.texto };
    case "error":
      return { ...m, error: ev.mensaje };
    case "fin":
      return { ...m, pendiente: false };
  }
}

/** Se puede valorar una respuesta completa del asistente que salió de los manuales (no las de cortesía). */
export const esValorable = (m: Mensaje) =>
  m.role === "assistant" && !m.pendiente && !m.interrumpida && !m.error && !!m.plan && !!m.content;

/**
 * Estado y acciones del chat. El historial activo se guarda en Redis por conversacionId.
 * onAprendizaje: avisa que cambió la memoria (para actualizar la barra lateral).
 */
export function useChat(onAprendizaje?: () => void) {
  const [mensajes, setMensajes] = useState<Mensaje[]>([]);
  const [conversacionId, setConversacionId] = useState(obtenerConversacionId);
  const [cargandoHistorial, setCargandoHistorial] = useState(true);
  const [enviando, setEnviando] = useState(false);
  const controlador = useRef<AbortController | null>(null);

  useEffect(() => {
    let vigente = true;
    setCargandoHistorial(true);
    api
      .conversacion(conversacionId)
      .then((guardados) => {
        if (vigente) setMensajes(guardados);
      })
      .catch(() => {
        if (vigente) setMensajes([]);
      })
      .finally(() => {
        if (vigente) setCargandoHistorial(false);
      });
    return () => {
      vigente = false;
    };
  }, [conversacionId]);

  const actualizar = (id: string, cambio: (m: Mensaje) => Mensaje) =>
    setMensajes((prev) => prev.map((m) => (m.id === id ? cambio(m) : m)));

  const enviar = useCallback(
    async (texto: string, opciones: OpcionesChat) => {
      const pregunta = texto.trim();
      if (!pregunta || enviando || cargandoHistorial) return;

      const idUsuario = nuevoId();
      const idRespuesta = nuevoId();
      setMensajes((prev) => [
        ...prev,
        { id: idUsuario, role: "user", content: pregunta },
        { id: idRespuesta, role: "assistant", content: "", pendiente: true, fuentes: [] },
      ]);
      setEnviando(true);
      controlador.current = new AbortController();

      let completa = false; // si se detiene la generación no llega "fin" y la respuesta no se puede validar
      try {
        const eventos = consultaStream(
          {
            mensaje: pregunta,
            conversacion_id: conversacionId,
            id_usuario: idUsuario,
            id_asistente: idRespuesta,
            manual: opciones.manual,
            k: opciones.k,
          },
          controlador.current.signal,
        );
        for await (const ev of eventos) {
          if (ev.tipo === "fin") completa = true;
          actualizar(idRespuesta, (m) => aplicarEvento(m, ev));
        }
      } catch (err) {
        actualizar(idRespuesta, (m) => ({ ...m, error: (err as Error).message }));
      } finally {
        actualizar(idRespuesta, (m) => ({ ...m, pendiente: false, interrumpida: !completa }));
        setEnviando(false);
        controlador.current = null;
      }
    },
    [cargandoHistorial, conversacionId, enviando],
  );

  const detener = useCallback(() => controlador.current?.abort(), []);

  const nuevaConversacion = useCallback(() => {
    controlador.current?.abort();
    setCargandoHistorial(true);
    setMensajes([]);
    const id = nuevoId();
    setConversacionId(id);
    try {
      window.localStorage.setItem(CLAVE_CONVERSACION, id);
    } catch {
      // La conversación sigue funcionando en memoria aunque el navegador no permita localStorage.
    }
  }, []);

  /** 👍 / 👎. Volver a tocar el mismo botón quita la valoración. */
  const valorar = useCallback(
    async (mensaje: Mensaje, valor: Valoracion) => {
      if (!esValorable(mensaje) || mensaje.guardandoValoracion) return;
      const nueva = mensaje.valoracion === valor ? null : valor;
      const anterior = mensaje.valoracion ?? null;
      actualizar(mensaje.id, (m) => ({ ...m, valoracion: nueva, guardandoValoracion: true, errorValoracion: undefined }));
      try {
        if (nueva === "positiva") {
          await api.aprender({
            id: mensaje.id,
            consulta: mensaje.plan!.consulta,
            respuesta: mensaje.content,
            fuentes: (mensaje.fuentes ?? []).map((f) => f.id),
          });
        } else if (anterior === "positiva") {
          await api.olvidar(mensaje.id);
        }
        actualizar(mensaje.id, (m) => ({ ...m, guardandoValoracion: false }));
        if (nueva === "positiva" || anterior === "positiva") onAprendizaje?.();
      } catch (err) {
        actualizar(mensaje.id, (m) => ({
          ...m,
          valoracion: anterior,
          guardandoValoracion: false,
          errorValoracion: (err as Error).message,
        }));
      }
    },
    [onAprendizaje],
  );

  /** Se olvidó una consulta desde la página Aprendizaje: si está en el chat, se le quita el 👍. */
  const olvidada = useCallback((id: string) => {
    setMensajes((prev) => prev.map((m) => (m.id === id && m.valoracion === "positiva" ? { ...m, valoracion: null } : m)));
  }, []);

  return { mensajes, enviando, cargandoHistorial, enviar, detener, nuevaConversacion, valorar, olvidada };
}
