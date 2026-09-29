import { AlertTriangle, BookOpen, Bot, GraduationCap, ThumbsDown, ThumbsUp, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Fuente, Mensaje, Plan, Recuerdo, Valoracion } from "../types";
import { esValorable } from "../useChat";

const ORIGEN: Record<NonNullable<Plan["origen"]>, string> = {
  elegido: "elegido por vos",
  detectado: "detectado en la pregunta",
  contexto: "por el contexto de la conversación",
  aprendido: "aprendido de una consulta validada",
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

/** Consultas validadas parecidas que se usaron para responder. */
function Recuerdos({ recuerdos }: { recuerdos: Recuerdo[] }) {
  if (!recuerdos.length) return null;
  const detalle = recuerdos.map((r) => `«${r.consulta}» (similitud ${r.similitud.toFixed(2)})`).join("\n");
  return (
    <p className="plan plan-memoria" title={detalle}>
      <GraduationCap size={13} />
      Usó {recuerdos.length === 1 ? "1 consulta validada parecida" : `${recuerdos.length} consultas validadas parecidas`}
      {" · "}similitud {recuerdos[0].similitud.toFixed(2)}
    </p>
  );
}

interface PropsValoracion {
  mensaje: Mensaje;
  onValorar: (m: Mensaje, v: Valoracion) => void;
}

/** 👍 guarda la consulta en la memoria del sistema; 👎 (o volver a tocar 👍) la quita. */
function Valorar({ mensaje, onValorar }: PropsValoracion) {
  const { valoracion, guardandoValoracion: guardando } = mensaje;
  return (
    <div className="valoracion">
      <button
        className={`boton-valorar ${valoracion === "positiva" ? "activo-positivo" : ""}`}
        onClick={() => onValorar(mensaje, "positiva")}
        disabled={guardando}
        aria-pressed={valoracion === "positiva"}
        title="Respuesta correcta: el asistente la aprende y la usa en consultas parecidas"
      >
        <ThumbsUp size={14} />
      </button>
      <button
        className={`boton-valorar ${valoracion === "negativa" ? "activo-negativo" : ""}`}
        onClick={() => onValorar(mensaje, "negativa")}
        disabled={guardando}
        aria-pressed={valoracion === "negativa"}
        title="Respuesta incorrecta: no se aprende"
      >
        <ThumbsDown size={14} />
      </button>
      <span className="tenue">
        {guardando
          ? "Guardando…"
          : valoracion === "positiva"
            ? "Aprendida: se va a usar en consultas parecidas"
            : valoracion === "negativa"
              ? "No se va a aprender"
              : "¿Te sirvió la respuesta?"}
      </span>
      {mensaje.errorValoracion && <span className="valoracion-error">{mensaje.errorValoracion}</span>}
    </div>
  );
}

function TarjetaFuente({ fuente, indice }: { fuente: Fuente; indice: number }) {
  const puntajes = [
    fuente.score_vectorial != null && `similitud ${fuente.score_vectorial.toFixed(2)}`,
    fuente.score_bm25 != null && `BM25 ${fuente.score_bm25.toFixed(1)}`,
    fuente.score_memoria != null && `memoria ${fuente.score_memoria.toFixed(2)}`,
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

export default function MensajeChat({ mensaje, onValorar }: PropsValoracion) {
  const esUsuario = mensaje.role === "user";
  const escribiendo = mensaje.pendiente && !mensaje.content;
  return (
    <div className={`mensaje ${esUsuario ? "mensaje-usuario" : "mensaje-asistente"}`}>
      <div className="avatar">{esUsuario ? <User size={18} /> : <Bot size={18} />}</div>
      <div className="burbuja">
        {mensaje.plan && <PlanManual plan={mensaje.plan} />}
        {mensaje.recuerdos && <Recuerdos recuerdos={mensaje.recuerdos} />}
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
        {esValorable(mensaje) && <Valorar mensaje={mensaje} onValorar={onValorar} />}
      </div>
    </div>
  );
}
