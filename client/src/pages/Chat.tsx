import { Plus, Send, Square } from "lucide-react";
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import MensajeChat from "../components/MensajeChat";
import type { OpcionesChat, useChat } from "../useChat";

const SUGERENCIAS = [
  { icono: "📟", texto: "¿Qué significa la alarma A01 del compresor y cómo la soluciono?" },
  { icono: "🛢️", texto: "¿Cada cuántas horas se cambia el aceite del compresor y qué aceite lleva?" },
  { icono: "⚙️", texto: "El torno marca la alarma AL-205, ¿qué hago?" },
  { icono: "🌡️", texto: "¿A qué temperatura se procesa el ABS en la inyectora?" },
  { icono: "🔩", texto: "¿Qué torque llevan los bulones M16 de la cinta transportadora?" },
  { icono: "🔒", texto: "¿Cuáles son los pasos del bloqueo y etiquetado (LOTO)?" },
];

interface Props {
  chat: ReturnType<typeof useChat>;
  opciones: OpcionesChat;
  setOpciones: (o: OpcionesChat) => void;
  manuales: string[];
}

export default function Chat({ chat, opciones, setOpciones, manuales }: Props) {
  const [texto, setTexto] = useState("");
  const finRef = useRef<HTMLDivElement>(null);
  const { mensajes, enviando, enviar, detener, nuevaConversacion, valorar } = chat;

  // Desplazar al último mensaje mientras llega la respuesta
  const ultimo = mensajes[mensajes.length - 1];
  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [mensajes.length, ultimo?.content]);

  const mandar = (t: string) => {
    if (!t.trim() || enviando) return;
    enviar(t, opciones);
    setTexto("");
  };

  const alPresionar = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      mandar(texto);
    }
  };

  return (
    <div className="chat">
      <header className="chat-cabecera">
        <div>
          <h1>Consulta de manuales</h1>
        </div>
        <div className="controles">
          <select
            value={opciones.manual ?? ""}
            onChange={(e) => setOpciones({ ...opciones, manual: e.target.value || null })}
            aria-label="Manual"
            title="Automático: el sistema detecta de qué máquina hablás"
          >
            <option value="">Manual: automático</option>
            {manuales.map((m) => (
              <option key={m} value={m}>
                Solo {m}
              </option>
            ))}
          </select>
          <label className="control-k" title="Fragmentos de manual que se envían al modelo">
            k
            <input
              type="number"
              min={1}
              max={10}
              value={opciones.k}
              onChange={(e) => setOpciones({ ...opciones, k: Math.min(10, Math.max(1, Number(e.target.value) || 1)) })}
            />
          </label>
          <button
            className="boton-secundario"
            onClick={nuevaConversacion}
            title="Nueva conversación (la actual no se guarda; lo validado con 👍 queda aprendido)"
          >
            <Plus size={15} /> Nueva
          </button>
        </div>
      </header>

      <section className="mensajes">
        {mensajes.length === 0 ? (
          <div className="bienvenida">
            <h2>¿Qué querés consultar?</h2>
            <p className="tenue">
              Cada consulta usa una sola llamada al modelo. Marcá 👍 las respuestas correctas: el asistente las aprende y
              las usa en consultas parecidas.
            </p>
            <div className="sugerencias">
              {SUGERENCIAS.map((s) => (
                <button key={s.texto} className="sugerencia" onClick={() => mandar(s.texto)}>
                  <span>{s.icono}</span>
                  {s.texto}
                </button>
              ))}
            </div>
          </div>
        ) : (
          mensajes.map((m) => <MensajeChat key={m.id} mensaje={m} onValorar={valorar} />)
        )}
        <div ref={finRef} />
      </section>

      <footer className="entrada">
        <textarea
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          onKeyDown={alPresionar}
          placeholder="Escribí tu consulta… (ej: el torno marca AL-205)"
          rows={1}
          maxLength={2000}
        />
        {enviando ? (
          <button className="boton-enviar detener" onClick={detener} title="Detener">
            <Square size={18} />
          </button>
        ) : (
          <button className="boton-enviar" onClick={() => mandar(texto)} disabled={!texto.trim()} title="Enviar (Enter)">
            <Send size={18} />
          </button>
        )}
      </footer>
    </div>
  );
}
