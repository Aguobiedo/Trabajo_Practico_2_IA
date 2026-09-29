import { useCallback, useRef, useState } from "react";
import { api, consultaStream } from "./api";
import type { EventoConsulta, Mensaje, Valoracion } from "./types";

export interface OpcionesChat {
  k: number;
  manual: string | null; // null = detección automática del manual
}

const nuevoId = () => crypto.randomUUID();

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
 * Estado y acciones del chat. Vive en App para que la conversación no se pierda al cambiar de página.
 * La conversación no se guarda en el server: solo lo que se valida con 👍 pasa a la memoria del sistema.
 * onAprendizaje: avisa que cambió la memoria (para actualizar la barra lateral).
 */
export function useChat(onAprendizaje?: () => void) {
  const [mensajes, setMensajes] = useState<Mensaje[]>([]);
  const [enviando, setEnviando] = useState(false);
  const controlador = useRef<AbortController | null>(null);

  const actualizar = (id: string, cambio: (m: Mensaje) => Mensaje) =>
    setMensajes((prev) => prev.map((m) => (m.id === id ? cambio(m) : m)));

  const enviar = useCallback(
    async (texto: string, opciones: OpcionesChat) => {
      const pregunta = texto.trim();
      if (!pregunta || enviando) return;

      // La conversación previa viaja en cada consulta: el server no guarda estado
      const historial = mensajes
        .filter((m) => !m.error && !m.pendiente && m.content)
        .map(({ role, content }) => ({ role, content }));

      const idRespuesta = nuevoId();
      setMensajes((prev) => [
        ...prev,
        { id: nuevoId(), role: "user", content: pregunta },
        { id: idRespuesta, role: "assistant", content: "", pendiente: true, fuentes: [] },
      ]);
      setEnviando(true);
      controlador.current = new AbortController();

      let completa = false; // si se detiene la generación no llega "fin" y la respuesta no se puede validar
      try {
        const eventos = consultaStream(
          { mensaje: pregunta, historial, manual: opciones.manual, k: opciones.k },
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
    [enviando, mensajes],
  );

  const detener = useCallback(() => controlador.current?.abort(), []);

  const nuevaConversacion = useCallback(() => {
    controlador.current?.abort();
    setMensajes([]);
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

  return { mensajes, enviando, enviar, detener, nuevaConversacion, valorar, olvidada };
}
