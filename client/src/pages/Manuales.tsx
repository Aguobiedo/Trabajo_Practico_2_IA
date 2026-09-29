import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { CheckCircle2, FileText, Plus, X } from "lucide-react";
import { api } from "../api";
import SubirManual from "../components/SubirManual";
import type { ContenidoManual, Manual, ManualSubido } from "../types";

interface Props {
  onCambio: () => void; // avisa que cambió el índice (para actualizar el estado de la barra lateral)
}

export default function Manuales({ onCambio }: Props) {
  const [manuales, setManuales] = useState<Manual[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [seleccionado, setSeleccionado] = useState<string>("");
  const [contenido, setContenido] = useState<ContenidoManual | null>(null);
  const [version, setVersion] = useState(0); // para volver a cargar el visor si se reemplaza el manual abierto
  const [subiendo, setSubiendo] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);
  const visor = useRef<HTMLDivElement>(null);

  const cargarManuales = useCallback(() => {
    api
      .manuales()
      .then((lista) => {
        setManuales(lista);
        setSeleccionado((s) => s || lista[0]?.archivo || "");
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  useEffect(cargarManuales, [cargarManuales]);

  useEffect(() => {
    if (!seleccionado) return;
    api
      .verManual(seleccionado)
      .then(setContenido)
      .catch((e: Error) => setError(e.message));
  }, [seleccionado, version]);

  const elegir = (archivo: string) => {
    setSeleccionado(archivo);
    // en pantallas chicas el visor queda debajo de la lista
    if (window.matchMedia("(max-width: 1100px)").matches) {
      visor.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const alSubir = (m: ManualSubido) => {
    setSubiendo(false);
    setAviso(`${m.reemplazado ? "Se reemplazó" : "Se agregó"} ${m.archivo} (${m.modelo}): ${m.chunks} fragmentos indexados.`);
    cargarManuales();
    setSeleccionado(m.archivo);
    setVersion((v) => v + 1);
    onCambio();
  };

  const actual = manuales.find((m) => m.archivo === seleccionado);

  return (
    <div className="pagina">
      <header className="pagina-cabecera">
        <div>
          <h1>Manuales técnicos</h1>
          <p className="tenue">Base de conocimiento del RAG. Cada manual se divide en fragmentos (chunks) con embeddings.</p>
        </div>
        {!subiendo && (
          <button
            className="boton-primario"
            onClick={() => {
              setSubiendo(true);
              setAviso(null);
            }}
          >
            <Plus size={16} /> Agregar manual
          </button>
        )}
      </header>

      {error && <div className="aviso aviso-error">{error}</div>}
      {aviso && (
        <div className="aviso aviso-ok">
          <CheckCircle2 size={16} />
          <span>{aviso}</span>
          <button className="boton-icono cerrar-aviso" onClick={() => setAviso(null)} aria-label="Cerrar aviso">
            <X size={14} />
          </button>
        </div>
      )}

      {subiendo && <SubirManual onSubido={alSubir} onCerrar={() => setSubiendo(false)} />}

      <div className="manuales-layout">
        <section className="lista-manuales" aria-label="Manuales cargados">
          <h3 className="lista-titulo">
            {manuales.length} {manuales.length === 1 ? "manual" : "manuales"}
          </h3>
          {manuales.map((m) => (
            <button
              key={m.archivo}
              className={`manual-item ${m.archivo === seleccionado ? "activo" : ""}`}
              onClick={() => elegir(m.archivo)}
            >
              <span className="manual-icono">
                <FileText size={18} />
              </span>
              <span className="manual-datos">
                <span className="manual-fila">
                  <strong>{m.modelo}</strong>
                  <span className="chip">{m.chunks} chunks</span>
                </span>
                <span className="manual-equipo">{m.equipo}</span>
                <small className="tenue">{m.archivo}</small>
              </span>
            </button>
          ))}
        </section>

        <section className="tarjeta visor-tarjeta" ref={visor}>
          {actual && (
            <div className="visor-cabecera">
              <strong>{actual.equipo}</strong>
              <small className="tenue">
                {actual.modelo} · {actual.archivo}
              </small>
            </div>
          )}
          <div className="visor markdown">
            {contenido ? (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{contenido.contenido}</ReactMarkdown>
            ) : (
              <p className="tenue">Seleccioná un manual.</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
