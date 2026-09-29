import { AlertTriangle, BookOpen, MessageSquare, RefreshCw, Wrench } from "lucide-react";
import type { Estado } from "../types";

export type Pagina = "consultas" | "manuales";

const ITEMS: { id: Pagina; titulo: string; icono: typeof MessageSquare }[] = [
  { id: "consultas", titulo: "Consultas", icono: MessageSquare },
  { id: "manuales", titulo: "Manuales", icono: BookOpen },
];

interface Props {
  pagina: Pagina;
  onNavegar: (p: Pagina) => void;
  estado: Estado | null;
  error: string | null;
  onReintentar: () => void;
}

export default function Sidebar({ pagina, onNavegar, estado, error, onReintentar }: Props) {
  return (
    <aside className="sidebar">
      <div className="marca">
        <span className="marca-logo">
          <Wrench size={20} />
        </span>
        <div>
          <strong>Asistente de Mantenimiento</strong>
          <small>Consulta de manuales técnicos</small>
        </div>
      </div>

      <nav className="nav">
        {ITEMS.map(({ id, titulo, icono: Icono }) => (
          <button key={id} className={`nav-item ${pagina === id ? "activo" : ""}`} onClick={() => onNavegar(id)}>
            <Icono size={18} />
            <span>{titulo}</span>
          </button>
        ))}
      </nav>

      <section className="estado-sistema">
        <h4>Estado del sistema</h4>
        {error ? (
          <div className="aviso aviso-error">
            <AlertTriangle size={16} />
            <span>{error}</span>
            <button className="boton-link" onClick={onReintentar}>
              <RefreshCw size={14} /> Reintentar
            </button>
          </div>
        ) : !estado ? (
          <p className="tenue">Conectando con el server…</p>
        ) : (
          <dl>
            <dt>Modelo</dt>
            <dd>
              <code>{estado.modelo}</code>
            </dd>
            <dt>Índice</dt>
            <dd>
              {estado.chunks} fragmentos · {estado.manuales.length} manuales
            </dd>
          </dl>
        )}
      </section>
      <p className="pie">LangChain · Gemini · Chroma · FastAPI · React</p>
    </aside>
  );
}
