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
  score_memoria: number | null; // similitud de la consulta validada que citó este fragmento
}

/** Decisión tomada antes de buscar: en qué manual y con qué texto. */
export interface Plan {
  consulta: string;
  manual: string | null;
  origen: "elegido" | "detectado" | "contexto" | "aprendido" | null;
}

/** Consulta validada parecida que el sistema usó para responder. */
export interface Recuerdo {
  id: string;
  consulta: string;
  manual: string | null;
  similitud: number;
}

export type Valoracion = "positiva" | "negativa" | null;

export interface Mensaje {
  id: string;
  role: "user" | "assistant";
  content: string;
  plan?: Plan;
  recuerdos?: Recuerdo[];
  fuentes?: Fuente[];
  error?: string;
  pendiente?: boolean;
  interrumpida?: boolean; // el usuario detuvo la generación
  valoracion?: Valoracion;
  guardandoValoracion?: boolean;
  errorValoracion?: string;
}

// Eventos del stream NDJSON de POST /api/consulta
export type EventoConsulta =
  | ({ tipo: "plan" } & Plan)
  | { tipo: "memoria"; recuerdos: Recuerdo[] }
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
  aprendidas: number;
}

/** 👍: lo que el server necesita para aprender una respuesta. */
export interface ConsultaValidada {
  id: string;
  consulta: string; // texto que se buscó (plan.consulta)
  respuesta: string;
  fuentes: (string | null)[]; // ids de los fragmentos, en el orden de las citas [1], [2]...
}

/** Consulta guardada en la memoria del sistema (GET /api/aprendizaje). */
export interface ConsultaAprendida {
  id: string;
  consulta: string;
  respuesta: string;
  manual: string | null;
  fragmentos: string[];
  fecha: string;
}

export interface Manual {
  modelo: string;
  equipo: string;
  archivo: string;
  chunks: number;
}

export interface ManualSubido extends Manual {
  reemplazado: boolean;
}

export interface ContenidoManual {
  archivo: string;
  contenido: string;
}
