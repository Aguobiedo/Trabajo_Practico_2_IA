// Tipos de las respuestas JSON del server (server/main.py)

export interface Fuente {
  id: string | null;
  modelo: string;
  equipo: string;
  archivo: string;
  seccion: string;
  contenido: string;
  score_vectorial: number | null;
  score_bm25: number | null;
}

/** Decisión tomada antes de buscar: en qué manual y con qué texto. */
export interface Plan {
  consulta: string;
  manual: string | null;
  origen: "elegido" | "detectado" | "contexto" | null;
}

export interface Mensaje {
  id: string;
  role: "user" | "assistant";
  content: string;
  plan?: Plan;
  fuentes?: Fuente[];
  error?: string;
  pendiente?: boolean;
}

// Eventos del stream NDJSON de POST /api/consulta
export type EventoConsulta =
  | ({ tipo: "plan" } & Plan)
  | { tipo: "fuentes"; fuentes: Fuente[] }
  | { tipo: "token"; texto: string }
  | { tipo: "error"; mensaje: string }
  | { tipo: "fin" };

export interface ConsultaRequest {
  mensaje: string;
  historial: { role: "user" | "assistant"; content: string }[];
  manual: string | null;
  k: number;
}

export interface Estado {
  modelo: string;
  top_k: number;
  listo: boolean;
  error: string | null;
  chunks: number;
  manuales: string[];
}

export interface Manual {
  modelo: string;
  equipo: string;
  archivo: string;
  chunks: number;
}

export interface ContenidoManual {
  archivo: string;
  contenido: string;
}
