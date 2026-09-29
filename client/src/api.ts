// Cliente HTTP de la API. Todas las rutas son relativas (/api/...): en desarrollo
// Vite las reenvía al server FastAPI (ver vite.config.ts).
import type { ConsultaRequest, ContenidoManual, Estado, EventoConsulta, Manual, ManualSubido } from "./types";

const SIN_CONEXION = "No se pudo conectar con el server. ¿Está corriendo en el puerto 8000?";

async function pedir<T>(url: string, init?: RequestInit): Promise<T> {
  let resp: Response;
  try {
    resp = await fetch(url, init);
  } catch {
    throw new Error(SIN_CONEXION);
  }
  if (!resp.ok) {
    let detalle = `${resp.status} ${resp.statusText}`;
    try {
      const cuerpo = await resp.json();
      if (cuerpo?.detail) detalle = typeof cuerpo.detail === "string" ? cuerpo.detail : JSON.stringify(cuerpo.detail);
    } catch {
      /* respuesta sin JSON (p. ej. el proxy de Vite sin server) */
      if (resp.status >= 500) detalle = SIN_CONEXION;
    }
    throw new Error(detalle);
  }
  return resp.json() as Promise<T>;
}

export const api = {
  estado: () => pedir<Estado>("/api/estado"),
  manuales: () => pedir<Manual[]>("/api/manuales"),
  verManual: (archivo: string) => pedir<ContenidoManual>(`/api/manuales/${encodeURIComponent(archivo)}`),
  // multipart/form-data: el navegador arma el Content-Type con el boundary
  subirManual: (datos: FormData) => pedir<ManualSubido>("/api/manuales", { method: "POST", body: datos }),
};

/**
 * Envía una consulta y va devolviendo los eventos a medida que llegan.
 * El server responde NDJSON: un objeto JSON por línea.
 */
export async function* consultaStream(cuerpo: ConsultaRequest, signal?: AbortSignal): AsyncGenerator<EventoConsulta> {
  let resp: Response;
  try {
    resp = await fetch("/api/consulta", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cuerpo),
      signal,
    });
  } catch (err) {
    if ((err as Error).name === "AbortError") return;
    throw new Error(SIN_CONEXION);
  }
  if (!resp.ok || !resp.body) {
    let detalle = `${resp.status} ${resp.statusText}`;
    try {
      detalle = (await resp.json()).detail ?? detalle;
    } catch {
      if (resp.status >= 500) detalle = SIN_CONEXION;
    }
    throw new Error(detalle);
  }

  const lector = resp.body.getReader();
  const decodificador = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { done, value } = await lector.read();
      if (done) break;
      buffer += decodificador.decode(value, { stream: true });
      let salto: number;
      while ((salto = buffer.indexOf("\n")) >= 0) {
        const linea = buffer.slice(0, salto).trim();
        buffer = buffer.slice(salto + 1);
        if (linea) yield JSON.parse(linea) as EventoConsulta;
      }
    }
    if (buffer.trim()) yield JSON.parse(buffer) as EventoConsulta;
  } catch (err) {
    if ((err as Error).name !== "AbortError") throw err;
  }
}
