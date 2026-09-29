import { useCallback, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { GraduationCap, Trash2 } from "lucide-react";
import { api } from "../api";
import type { ConsultaAprendida } from "../types";

interface Props {
  onOlvidada: (id: string) => void; // avisa que se quitó una consulta de la memoria
}

const formatoFecha = new Intl.DateTimeFormat("es-AR", { dateStyle: "short", timeStyle: "short" });

/** "IP-250_inyectora_plastimaq.md::003" -> "IP-250_inyectora_plastimaq.md · fragmento 3" */
const nombreFragmento = (id: string) => {
  const [archivo, n] = id.split("::");
  return n ? `${archivo} · fragmento ${Number(n)}` : id;
};

export default function Aprendizaje({ onOlvidada }: Props) {
  const [consultas, setConsultas] = useState<ConsultaAprendida[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [olvidando, setOlvidando] = useState<string | null>(null);

  const cargar = useCallback(() => {
    api
      .aprendizaje()
      .then(setConsultas)
      .catch((e: Error) => setError(e.message));
  }, []);

  useEffect(cargar, [cargar]);

  const olvidar = async (id: string) => {
    setOlvidando(id);
    setError(null);
    try {
      await api.olvidar(id);
      setConsultas((lista) => lista?.filter((c) => c.id !== id) ?? null);
      onOlvidada(id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setOlvidando(null);
    }
  };

  return (
    <div className="pagina">
      <header className="pagina-cabecera">
        <div>
          <h1>Aprendizaje</h1>
          <p className="tenue">
            Consultas que marcaste con 👍. Las conversaciones no se guardan: el asistente solo recuerda estas preguntas
            con su respuesta. Ante una consulta parecida las usa para elegir el manual, priorizar los fragmentos que
            sirvieron y como ejemplo para el modelo.
          </p>
        </div>
      </header>

      {error && <div className="aviso aviso-error">{error}</div>}

      {consultas === null ? (
        !error && <p className="tenue">Cargando…</p>
      ) : consultas.length === 0 ? (
        <div className="tarjeta vacio">
          <GraduationCap size={28} />
          <strong>Todavía no aprendió nada</strong>
          <p className="tenue">En la página Consultas, marcá 👍 en las respuestas correctas para que el asistente las recuerde.</p>
        </div>
      ) : (
        <section className="lista-aprendidas" aria-label="Consultas aprendidas">
          <h3 className="lista-titulo">
            {consultas.length} {consultas.length === 1 ? "consulta validada" : "consultas validadas"}
          </h3>
          {consultas.map((c) => (
            <article key={c.id} className="tarjeta aprendida">
              <header className="aprendida-cabecera">
                <div>
                  <strong>{c.consulta}</strong>
                  <small className="tenue">
                    {c.manual ? `Manual ${c.manual}` : "Sin manual único"} · {formatoFecha.format(new Date(c.fecha))}
                  </small>
                </div>
                <button
                  className="boton-secundario"
                  onClick={() => olvidar(c.id)}
                  disabled={olvidando === c.id}
                  title="Quitar de la memoria"
                >
                  <Trash2 size={15} /> Olvidar
                </button>
              </header>
              <details className="plegable">
                <summary>Respuesta validada</summary>
                <div className="markdown aprendida-respuesta">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{c.respuesta}</ReactMarkdown>
                </div>
              </details>
              {c.fragmentos.length > 0 && (
                <div className="chips">
                  {c.fragmentos.map((f) => (
                    <span key={f} className="chip" title="Fragmento citado en la respuesta validada">
                      {nombreFragmento(f)}
                    </span>
                  ))}
                </div>
              )}
            </article>
          ))}
        </section>
      )}
    </div>
  );
}
