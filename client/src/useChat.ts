import { useCallback, useRef, useState } from "react";
import { consultaStream } from "./api";
import type { EventoConsulta, Mensaje } from "./types";

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

/** Estado y acciones del chat. Vive en App para que la conversación no se pierda al cambiar de página. */
export function useChat() {
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

      try {
        const eventos = consultaStream(
          { mensaje: pregunta, historial, manual: opciones.manual, k: opciones.k },
          controlador.current.signal,
        );
        for await (const ev of eventos) actualizar(idRespuesta, (m) => aplicarEvento(m, ev));
      } catch (err) {
        actualizar(idRespuesta, (m) => ({ ...m, error: (err as Error).message }));
      } finally {
        actualizar(idRespuesta, (m) => ({ ...m, pendiente: false }));
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

  return { mensajes, enviando, enviar, detener, nuevaConversacion };
}
