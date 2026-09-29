import { AlertTriangle, BookOpen, Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Fuente, Mensaje, Plan } from "../types";

const ORIGEN: Record<NonNullable<Plan["origen"]>, string> = {
  elegido: "elegido por vos",
  detectado: "detectado en la pregunta",
  contexto: "por el contexto de la conversación",
};

/** Qué decidió el sistema antes de buscar: en qué manual. */
function PlanManual({ plan }: { plan: Plan }) {
  return (
    <p className="plan">
      <BookOpen size={13} />
      {plan.manual ? (
        <>
          Manual <strong>{plan.manual}</strong> · {plan.origen ? ORIGEN[plan.origen] : ""}
        </>
      ) : (
        "Búsqueda en todos los manuales"
      )}
    </p>
  );
}

function TarjetaFuente({ fuente, indice }: { fuente: Fuente; indice: number }) {
  const puntajes = [
    fuente.score_vectorial != null && `similitud ${fuente.score_vectorial.toFixed(2)}`,
    fuente.score_bm25 != null && `BM25 ${fuente.score_bm25.toFixed(1)}`,
  ].filter(Boolean);
  return (
    <article className="fuente">
      <header>
        <span className="fuente-num">{indice}</span>
        <strong>{fuente.modelo}</strong>
        <span className="fuente-seccion">{fuente.seccion}</span>
      </header>
      <p>{fuente.contenido.length > 420 ? `${fuente.contenido.slice(0, 420)}…` : fuente.contenido}</p>
      <footer>
        {fuente.archivo}
        {puntajes.length > 0 && ` · ${puntajes.join(" · ")}`}
      </footer>
    </article>
  );
}

function Fuentes({ fuentes }: { fuentes: Fuente[] }) {
  if (!fuentes.length) return null;
  return (
    <details className="plegable">
      <summary>
        <BookOpen size={14} /> Fragmentos consultados ({fuentes.length})
      </summary>
      <div className="fuentes">
        {fuentes.map((f, i) => (
          <TarjetaFuente key={f.id ?? i} fuente={f} indice={i + 1} />
        ))}
      </div>
    </details>
  );
}

export default function MensajeChat({ mensaje }: { mensaje: Mensaje }) {
  const esUsuario = mensaje.role === "user";
  const escribiendo = mensaje.pendiente && !mensaje.content;
  return (
    <div className={`mensaje ${esUsuario ? "mensaje-usuario" : "mensaje-asistente"}`}>
      <div className="avatar">{esUsuario ? <User size={18} /> : <Bot size={18} />}</div>
      <div className="burbuja">
        {mensaje.plan && <PlanManual plan={mensaje.plan} />}
        {escribiendo && (
          <div className="escribiendo" aria-label="Generando respuesta">
            <span />
            <span />
            <span />
          </div>
        )}
        {mensaje.content && (
          <div className="markdown">
            {esUsuario ? <p>{mensaje.content}</p> : <ReactMarkdown remarkPlugins={[remarkGfm]}>{mensaje.content}</ReactMarkdown>}
          </div>
        )}
        {mensaje.error && (
          <div className="aviso aviso-error">
            <AlertTriangle size={16} />
            <span>{mensaje.error}</span>
          </div>
        )}
        {!esUsuario && !mensaje.pendiente && <Fuentes fuentes={mensaje.fuentes ?? []} />}
      </div>
    </div>
  );
}
