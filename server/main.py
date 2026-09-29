"""API del Asistente de Mantenimiento con FastAPI. Usa el mismo código que el notebook (paquete asistente).

Ejecutar desde la carpeta server:
    .venv\\Scripts\\python -m uvicorn main:app --port 8000
"""

import json
import os
import threading
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from asistente.config import GEMINI_MODEL, MANUALES_DIR, TOP_K, get_llm
from asistente.ingesta import construir_indice, leer_front_matter, obtener_vectorstore
from asistente.rag import a_mensajes, cadena_respuesta, preparar_consulta
from asistente.recuperacion import RecuperadorHibrido, formatear_contexto

_lock = threading.Lock()
_recursos = None


def recursos():
    """Recuperador y LLM, que se crean una sola vez. Si el índice está vacío, lo construye."""
    global _recursos
    with _lock:
        if _recursos is None:
            if not os.getenv("GOOGLE_API_KEY"):
                raise HTTPException(503, "Falta GOOGLE_API_KEY en el archivo .env")
            vs = obtener_vectorstore()
            if not vs.get(include=[])["ids"]:
                construir_indice(vs)
            _recursos = {"recuperador": RecuperadorHibrido(vs), "llm": get_llm()}
        return _recursos


def precargar():
    try:
        recursos()
    except Exception:
        pass  # el error se muestra en /api/estado


@asynccontextmanager
async def lifespan(_app):
    # Carga el índice y el modelo en segundo plano: el server arranca enseguida
    threading.Thread(target=precargar, daemon=True).start()
    yield


app = FastAPI(title="API del Asistente de Mantenimiento", lifespan=lifespan)


def mensaje_error(exc):
    texto = str(exc)
    if "429" in texto or "RESOURCE_EXHAUSTED" in texto:
        return "Se alcanzó el límite de uso de la API de Gemini. Esperá un momento y volvé a intentar."
    return f"Ocurrió un error: {texto[:400]}"


@app.get("/api/estado")
def estado():
    info = {"modelo": GEMINI_MODEL, "top_k": TOP_K, "listo": False, "error": None, "chunks": 0, "manuales": []}
    try:
        recuperador = recursos()["recuperador"]
    except HTTPException as exc:
        info["error"] = exc.detail
    except Exception as exc:
        info["error"] = mensaje_error(exc)
    else:
        info.update(listo=True, chunks=len(recuperador.docs), manuales=recuperador.modelos)
    return info


class MensajeHistorial(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class Consulta(BaseModel):
    mensaje: str = Field(min_length=1, max_length=2000)
    historial: list[MensajeHistorial] = []  # la conversación la guarda el client
    manual: str | None = None  # None = el sistema detecta el manual
    k: int = Field(default=TOP_K, ge=1, le=10)


def eventos_consulta(req, recuperador, llm):
    """Mismos pasos que la cadena RAG del notebook, pero enviando cada parte apenas está lista."""
    historial = [m.model_dump() for m in req.historial]
    plan = preparar_consulta(req.mensaje, historial, recuperador, req.manual)
    yield {"tipo": "plan", **plan}

    docs = recuperador.buscar(plan["consulta"], k=req.k, modelo=plan["manual"])
    yield {"tipo": "fuentes", "fuentes": [
        {"id": d.id, **{c: d.metadata.get(c) for c in ("modelo", "equipo", "archivo", "seccion",
                                                          "score_vectorial", "score_bm25")},
         "contenido": d.page_content.split("\n", 1)[-1]}  # sin el encabezado [equipo | sección]
        for d in docs]}

    entrada = {"input": req.mensaje, "chat_history": a_mensajes(historial), "context": formatear_contexto(docs)}
    for texto in cadena_respuesta(llm).stream(entrada):
        yield {"tipo": "token", "texto": texto}


@app.post("/api/consulta")
def consulta(req: Consulta):
    """Responde en streaming: un evento JSON por línea (plan, fuentes, token..., fin)."""
    r = recursos()

    def generar():
        try:
            for ev in eventos_consulta(req, r["recuperador"], r["llm"]):
                yield json.dumps(ev, ensure_ascii=False) + "\n"
        except Exception as exc:
            yield json.dumps({"tipo": "error", "mensaje": mensaje_error(exc)}, ensure_ascii=False) + "\n"
        yield json.dumps({"tipo": "fin"}) + "\n"

    return StreamingResponse(generar(), media_type="application/x-ndjson")


@app.get("/api/manuales")
def listar_manuales():
    resumen = {}
    for d in recursos()["recuperador"].docs:
        m = d.metadata
        item = resumen.setdefault(m["archivo"], {"modelo": m["modelo"], "equipo": m["equipo"],
                                                 "archivo": m["archivo"], "chunks": 0})
        item["chunks"] += 1
    return sorted(resumen.values(), key=lambda x: x["modelo"])


@app.get("/api/manuales/{archivo}")
def ver_manual(archivo: str):
    ruta = MANUALES_DIR / archivo
    if ruta.name != archivo or not ruta.exists():  # solo nombres de archivo simples
        raise HTTPException(404, "El manual no existe")
    return {"archivo": archivo, "contenido": leer_front_matter(ruta.read_text(encoding="utf-8"))[1]}
