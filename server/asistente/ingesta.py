"""Ingesta de los manuales: carga, división en fragmentos (chunks) e índice en Chroma."""

import re
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from .config import CHROMA_DIR, CHUNK_OVERLAP, CHUNK_SIZE, COLLECTION_NAME, MANUALES_DIR, get_embeddings


def leer_front_matter(texto):
    """Separa el encabezado '--- clave: valor ---' del cuerpo del manual."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", texto, re.DOTALL)
    if not m:
        return {}, texto
    meta = {}
    for linea in m.group(1).splitlines():
        if ":" in linea:
            clave, valor = linea.split(":", 1)
            meta[clave.strip()] = valor.strip()
    return meta, texto[m.end():]


def cargar_manuales(directorio=MANUALES_DIR):
    docs = []
    for ruta in sorted(Path(directorio).glob("*.md")):
        meta, cuerpo = leer_front_matter(ruta.read_text(encoding="utf-8"))
        # la aclaración "Documento ficticio" no aporta nada técnico
        cuerpo = "\n".join(l for l in cuerpo.splitlines() if not l.startswith("> Documento ficticio"))
        docs.append(Document(page_content=cuerpo, metadata={
            "archivo": ruta.name,
            "modelo": meta.get("modelo", ruta.stem),
            "equipo": meta.get("equipo", ruta.stem),
            "alias": meta.get("alias", ""),
        }))
    return docs


splitter_secciones = MarkdownHeaderTextSplitter(headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")])
splitter_tamano = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP,
                                                 separators=["\n\n", "\n", ". ", " ", ""])


def dividir(docs):
    """Divide cada manual primero por secciones y después por tamaño.

    A cada chunk se le agrega al principio el equipo y la sección de donde sale,
    para que no quede un fragmento suelto que no dice de qué máquina habla.
    """
    chunks = []
    for doc in docs:
        secciones = splitter_secciones.split_text(doc.page_content)
        for s in secciones:
            titulos = [s.metadata[h] for h in ("h2", "h3") if h in s.metadata]
            s.metadata = {**doc.metadata, "seccion": " > ".join(titulos) or "General"}
        for n, chunk in enumerate(splitter_tamano.split_documents(secciones)):
            m = chunk.metadata
            chunk.page_content = f"[{m['equipo']} ({m['modelo']}) | {m['seccion']}]\n{chunk.page_content.strip()}"
            chunk.id = f"{m['archivo']}::{n:03d}"
            chunks.append(chunk)
    return chunks


def obtener_vectorstore():
    return Chroma(collection_name=COLLECTION_NAME, embedding_function=get_embeddings(),
                  persist_directory=str(CHROMA_DIR), collection_metadata={"hnsw:space": "cosine"})


def construir_indice(vs):
    """Borra el índice y vuelve a indexar todos los manuales. Devuelve la cantidad de chunks."""
    vs.reset_collection()
    chunks = dividir(cargar_manuales())
    vs.add_documents(chunks, ids=[c.id for c in chunks])
    return len(chunks)
