import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api } from "../api";
import type { ContenidoManual, Manual } from "../types";

export default function Manuales() {
  const [manuales, setManuales] = useState<Manual[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [seleccionado, setSeleccionado] = useState<string>("");
  const [contenido, setContenido] = useState<ContenidoManual | null>(null);

  useEffect(() => {
    api
      .manuales()
      .then((lista) => {
        setManuales(lista);
        setSeleccionado((s) => s || lista[0]?.archivo || "");
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!seleccionado) return;
    api
      .verManual(seleccionado)
      .then(setContenido)
      .catch((e: Error) => setError(e.message));
  }, [seleccionado]);

  return (
    <div className="pagina">
      <header className="pagina-cabecera">
        <h1>Manuales técnicos</h1>
        <p className="tenue">Base de conocimiento del RAG. Cada manual se divide en fragmentos (chunks) con embeddings.</p>
      </header>

      {error && <div className="aviso aviso-error">{error}</div>}

      <div className="tarjeta">
        <table className="tabla">
          <thead>
            <tr>
              <th>Modelo</th>
              <th>Equipo</th>
              <th>Archivo</th>
              <th className="num">Chunks</th>
            </tr>
          </thead>
          <tbody>
            {manuales.map((m) => (
              <tr key={m.archivo}>
                <td>
                  <strong>{m.modelo}</strong>
                </td>
                <td>{m.equipo}</td>
                <td className="tenue">{m.archivo}</td>
                <td className="num">{m.chunks}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="tarjeta">
        <div className="fila-titulo">
          <h3>Ver manual</h3>
          <select value={seleccionado} onChange={(e) => setSeleccionado(e.target.value)}>
            {manuales.map((m) => (
              <option key={m.archivo} value={m.archivo}>
                {m.modelo} · {m.archivo}
              </option>
            ))}
          </select>
        </div>
        <div className="visor markdown">
          {contenido ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{contenido.contenido}</ReactMarkdown>
          ) : (
            <p className="tenue">Seleccioná un manual.</p>
          )}
        </div>
      </div>
    </div>
  );
}
