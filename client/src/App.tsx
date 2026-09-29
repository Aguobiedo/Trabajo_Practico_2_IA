import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import Sidebar, { type Pagina } from "./components/Sidebar";
import Aprendizaje from "./pages/Aprendizaje";
import Chat from "./pages/Chat";
import Manuales from "./pages/Manuales";
import type { Estado } from "./types";
import { useChat, type OpcionesChat } from "./useChat";

const PAGINAS: Pagina[] = ["consultas", "manuales", "aprendizaje"];

// Navegación simple por hash (#consultas, #manuales, #aprendizaje): permite recargar la página actual
function paginaDesdeHash(): Pagina {
  const hash = window.location.hash.replace("#", "") as Pagina;
  return PAGINAS.includes(hash) ? hash : "consultas";
}

export default function App() {
  const [pagina, setPagina] = useState<Pagina>(paginaDesdeHash);
  const [estado, setEstado] = useState<Estado | null>(null);
  const [errorEstado, setErrorEstado] = useState<string | null>(null);
  const [opciones, setOpciones] = useState<OpcionesChat>({ k: 4, manual: null });
  const reintento = useRef<number | undefined>(undefined);

  // Si el server todavía está arrancando o se reinició, se reintenta solo cada 3 s
  const cargarEstado = useCallback(() => {
    window.clearTimeout(reintento.current);
    api
      .estado()
      .then((e) => {
        setEstado(e);
        setErrorEstado(e.error);
        setOpciones((o) => ({ ...o, k: e.top_k }));
      })
      .catch((err: Error) => {
        setErrorEstado(`${err.message} Reintentando…`);
        reintento.current = window.setTimeout(cargarEstado, 3000);
      });
  }, []);

  // cuando cambia la memoria (👍, 👎 u «Olvidar») se actualiza el contador de la barra lateral
  const chat = useChat(cargarEstado);

  useEffect(() => {
    cargarEstado();
    return () => window.clearTimeout(reintento.current);
  }, [cargarEstado]);

  useEffect(() => {
    const alCambiar = () => setPagina(paginaDesdeHash());
    window.addEventListener("hashchange", alCambiar);
    return () => window.removeEventListener("hashchange", alCambiar);
  }, []);

  const navegar = (p: Pagina) => {
    window.location.hash = p;
    setPagina(p);
  };

  return (
    <div className="app">
      <Sidebar pagina={pagina} onNavegar={navegar} estado={estado} error={errorEstado} onReintentar={cargarEstado} />
      <main className="contenido">
        {pagina === "consultas" && (
          <Chat chat={chat} opciones={opciones} setOpciones={setOpciones} manuales={estado?.manuales ?? []} />
        )}
        {pagina === "manuales" && <Manuales onCambio={cargarEstado} />}
        {pagina === "aprendizaje" && (
          <Aprendizaje
            onOlvidada={(id) => {
              chat.olvidada(id);
              cargarEstado();
            }}
          />
        )}
      </main>
    </div>
  );
}
