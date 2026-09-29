"""API del Asistente de Mantenimiento con FastAPI. Usa el mismo código que el notebook (paquete asistente).

Las conversaciones no se guardan: el historial vive en el client. Lo que se guarda es lo aprendido,
es decir, las consultas que el usuario validó con 👍 (colección "memoria" de Chroma).

Ejecutar desde la carpeta server:
    .venv\\Scripts\\python -m uvicorn main:app --port 8000
"""

import io
import json
import os
import re
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from pypdf import PdfReader

from asistente.config import GEMINI_MODEL, MANUALES_DIR, TOP_K, get_llm
from asistente.ingesta import construir_indice, indexar_manual, leer_front_matter, obtener_vectorstore
from asistente.memoria import obtener_memoria
from asistente.rag import (a_mensajes, cadena_respuesta, formatear_validadas, recuperar, respuesta_cortesia,
                           sin_cortesias)
from asistente.recuperacion import RecuperadorHibrido, formatear_contexto

_lock = threading.Lock()
_recursos = None


def recursos():
    """Recuperador, memoria y LLM, que se crean una sola vez. Si el índice está vacío, lo construye."""
    global _recursos
    with _lock:
        if _recursos is None:
            if not os.getenv("GOOGLE_API_KEY"):
                raise HTTPException(503, "Falta GOOGLE_API_KEY en el archivo .env")
            vs = obtener_vectorstore()
            if not vs.get(include=[])["ids"]:
                construir_indice(vs)
            _recursos = {"recuperador": RecuperadorHibrido(vs), "memoria": obtener_memoria(), "llm": get_llm()}
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
    info = {"modelo": GEMINI_MODEL, "top_k": TOP_K, "listo": False, "error": None, "chunks": 0, "manuales": [],
            "aprendidas": 0}
    try:
        r = recursos()
    except HTTPException as exc:
        info["error"] = exc.detail
    except Exception as exc:
        info["error"] = mensaje_error(exc)
    else:
        info.update(listo=True, chunks=len(r["recuperador"].docs), manuales=r["recuperador"].modelos,
                    aprendidas=len(r["memoria"]))
    return info


class MensajeHistorial(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class Consulta(BaseModel):
    mensaje: str = Field(min_length=1, max_length=2000)
    historial: list[MensajeHistorial] = []  # la conversación la guarda el client
    manual: str | None = None  # None = el sistema detecta el manual
    k: int = Field(default=TOP_K, ge=1, le=10)


def eventos_consulta(req, recuperador, memoria, llm):
    """Mismos pasos que la cadena RAG del notebook, pero enviando cada parte apenas está lista."""
    cortesia = respuesta_cortesia(req.mensaje)
    if cortesia:  # "ok", "gracias"...: respuesta fija, sin búsqueda ni LLM (no gasta tokens)
        yield {"tipo": "token", "texto": cortesia}
        return

    historial = sin_cortesias([m.model_dump() for m in req.historial])
    r = recuperar(req.mensaje, historial, recuperador, memoria, req.k, req.manual)
    yield {"tipo": "plan", **r["plan"]}
    yield {"tipo": "memoria", "recuerdos": [{c: x[c] for c in ("id", "consulta", "manual", "similitud")}
                                             for x in r["recuerdos"]]}
    yield {"tipo": "fuentes", "fuentes": [
        {"id": d.id, **{c: d.metadata.get(c) for c in ("modelo", "equipo", "archivo", "seccion",
                                                          "score_vectorial", "score_bm25", "score_memoria")},
         "contenido": d.page_content.split("\n", 1)[-1]}  # sin el encabezado [equipo | sección]
        for d in r["fuentes"]]}

    entrada = {"input": req.mensaje, "chat_history": a_mensajes(historial),
               "context": formatear_contexto(r["fuentes"]), "validadas": formatear_validadas(r["recuerdos"])}
    for texto in cadena_respuesta(llm).stream(entrada):
        yield {"tipo": "token", "texto": texto}


@app.post("/api/consulta")
def consulta(req: Consulta):
    """Responde en streaming: un evento JSON por línea (plan, memoria, fuentes, token..., fin)."""
    r = recursos()

    def generar():
        try:
            for ev in eventos_consulta(req, r["recuperador"], r["memoria"], r["llm"]):
                yield json.dumps(ev, ensure_ascii=False) + "\n"
        except Exception as exc:
            yield json.dumps({"tipo": "error", "mensaje": mensaje_error(exc)}, ensure_ascii=False) + "\n"
        yield json.dumps({"tipo": "fin"}) + "\n"

    return StreamingResponse(generar(), media_type="application/x-ndjson")


# --- Aprendizaje: consultas validadas por el usuario ---
class ConsultaValidada(BaseModel):
    id: str = Field(pattern=r"^[\w-]{1,64}$")  # id del mensaje en el client
    consulta: str = Field(min_length=1, max_length=4000)  # texto que se buscó (plan.consulta)
    respuesta: str = Field(min_length=1, max_length=12000)
    fuentes: list[str | None] = Field(default=[], max_length=10)  # ids de los fragmentos, en el orden [1], [2]...


@app.get("/api/aprendizaje")
def listar_aprendizaje():
    return recursos()["memoria"].listar()


@app.post("/api/aprendizaje", status_code=201)
def aprender(req: ConsultaValidada):
    """👍: guarda la consulta en la memoria (la vuelve a guardar si ya estaba)."""
    r = recursos()
    por_id = r["recuperador"].por_id
    # el manual de cada fragmento sale del índice, no de lo que manda el client
    fuentes = [{"id": f, "modelo": por_id[f].metadata["modelo"]} if f in por_id else None for f in req.fuentes]
    try:
        recuerdo = r["memoria"].aprender(req.id, req.consulta, req.respuesta, fuentes)
    except Exception as exc:
        raise HTTPException(502, mensaje_error(exc))
    return {"recuerdo": recuerdo, "aprendidas": len(r["memoria"])}


@app.delete("/api/aprendizaje/{id}")
def olvidar(id: str):
    """👎 o «Olvidar»: quita la consulta de la memoria (si no estaba, no hace nada)."""
    memoria = recursos()["memoria"]
    memoria.olvidar([id])
    return {"aprendidas": len(memoria)}


@app.get("/api/manuales")
def listar_manuales():
    resumen = {}
    for d in recursos()["recuperador"].docs:
        m = d.metadata
        item = resumen.setdefault(m["archivo"], {"modelo": m["modelo"], "equipo": m["equipo"],
                                                 "archivo": m["archivo"], "chunks": 0})
        item["chunks"] += 1
    return sorted(resumen.values(), key=lambda x: x["modelo"])


EXTENSIONES = {".md", ".txt", ".pdf"}
MAX_BYTES = 10 * 1024 * 1024


def texto_de_archivo(nombre, datos):
    """Texto del archivo subido. Los PDF se convierten a texto plano."""
    try:
        if nombre.lower().endswith(".pdf"):
            return "\n\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(datos)).pages)
        return datos.decode("utf-8-sig").replace("\r\n", "\n")
    except UnicodeDecodeError:
        raise HTTPException(400, "El archivo no está en UTF-8")
    except Exception:
        raise HTTPException(400, "No se pudo leer el archivo")


@app.post("/api/manuales", status_code=201)
def subir_manual(archivo: UploadFile = File(...), modelo: str = Form(""), equipo: str = Form(""),
                 alias: str = Form("")):
    """Guarda un manual (.md, .txt o .pdf) en data/manuales como .md y lo agrega al índice."""
    nombre = Path(archivo.filename or "").name
    if Path(nombre).suffix.lower() not in EXTENSIONES:
        raise HTTPException(400, "Formato no admitido. Subí un archivo .md, .txt o .pdf")
    datos = archivo.file.read(MAX_BYTES + 1)
    if len(datos) > MAX_BYTES:
        raise HTTPException(413, "El archivo supera los 10 MB")
    meta, cuerpo = leer_front_matter(texto_de_archivo(nombre, datos))
    if not cuerpo.strip():
        raise HTTPException(400, "El archivo no tiene texto (si es un PDF escaneado, no se puede leer)")

    # lo que se completa en el formulario tiene prioridad sobre el encabezado del archivo
    stem = re.sub(r"[^\w.-]+", "_", Path(nombre).stem).strip("._") or "manual"
    for clave, valor in (("modelo", modelo), ("equipo", equipo), ("alias", alias)):
        valor = " ".join(valor.split())  # una sola línea, para no romper el encabezado
        if valor:
            meta[clave] = valor
    meta.setdefault("modelo", stem)
    meta.setdefault("equipo", meta["modelo"])
    destino = MANUALES_DIR / f"{stem}.md"

    r = recursos()
    otro = next((d.metadata["archivo"] for d in r["recuperador"].docs
                 if d.metadata["modelo"] == meta["modelo"] and d.metadata["archivo"] != destino.name), None)
    if otro:
        raise HTTPException(409, f"El modelo {meta['modelo']} ya corresponde al manual {otro}")

    encabezado = "".join(f"{clave}: {valor}\n" for clave, valor in meta.items())
    with _lock:
        previo = destino.read_bytes() if destino.exists() else None
        destino.write_text(f"---\n{encabezado}---\n\n{cuerpo.strip()}\n", encoding="utf-8")
        try:
            chunks = indexar_manual(r["recuperador"].vs, destino)
        except Exception as exc:
            if previo is None:
                destino.unlink()
            else:
                destino.write_bytes(previo)
            raise HTTPException(502, mensaje_error(exc))
        r["recuperador"] = RecuperadorHibrido(r["recuperador"].vs)  # BM25 se rearma con el manual nuevo
    return {"archivo": destino.name, "modelo": meta["modelo"], "equipo": meta["equipo"], "chunks": chunks,
            "reemplazado": previo is not None}


@app.get("/api/manuales/{archivo}")
def ver_manual(archivo: str):
    ruta = MANUALES_DIR / archivo
    if ruta.name != archivo or not ruta.exists():  # solo nombres de archivo simples
        raise HTTPException(404, "El manual no existe")
    return {"archivo": archivo, "contenido": leer_front_matter(ruta.read_text(encoding="utf-8"))[1]}
