"""Aprendizaje: memoria de las consultas que el usuario validó (👍).

No se guardan las conversaciones, solo cada pregunta validada con su respuesta y los
fragmentos del manual que esa respuesta citó. Ante una pregunta parecida, la memoria sirve para:
1. elegir el manual cuando ninguna regla lo decidió (origen "aprendido");
2. sumar esos fragmentos a la búsqueda híbrida como una tercera lista de RRF;
3. pasarle al LLM las respuestas validadas como ejemplos.
"""

import re
from datetime import datetime

from langchain_chroma import Chroma
from langchain_core.documents import Document

from .config import CHROMA_DIR, MAX_RECUERDOS, UMBRAL_MEMORIA, get_embeddings

COLECCION_MEMORIA = "memoria"


def fragmentos_citados(respuesta, fuentes):
    """Fuentes que la respuesta citó con [n], en orden de aparición y sin repetir (None = fuente que ya no existe)."""
    citadas = []
    for n in re.findall(r"\[(\d+)\]", respuesta):
        i = int(n) - 1
        if 0 <= i < len(fuentes) and fuentes[i] and fuentes[i] not in citadas:
            citadas.append(fuentes[i])
    return citadas


class Memoria:
    def __init__(self, vectorstore, umbral=UMBRAL_MEMORIA, maximo=MAX_RECUERDOS):
        self.vs = vectorstore
        self.umbral = umbral
        self.maximo = maximo

    def __len__(self):
        return len(self.vs.get(include=[])["ids"])

    def aprender(self, id, consulta, respuesta, fuentes):
        """Guarda una consulta validada. fuentes: [{"id", "modelo"}] en el orden en que se enviaron al LLM.

        El manual aprendido es el de los fragmentos citados, si son todos del mismo.
        """
        citadas = fragmentos_citados(respuesta, fuentes)
        modelos = {f["modelo"] for f in citadas}
        self.vs.add_documents([Document(page_content=consulta, metadata={
            "respuesta": respuesta,
            "manual": modelos.pop() if len(modelos) == 1 else "",
            "fragmentos": ",".join(f["id"] for f in citadas),
            "fecha": datetime.now().isoformat(timespec="seconds"),
        })], ids=[id])
        return self.obtener(id)

    def olvidar(self, ids):
        if ids:
            self.vs.delete(ids=list(ids))

    @staticmethod
    def _recuerdo(id, texto, m, similitud=None):
        return {"id": id, "consulta": texto, "respuesta": m["respuesta"], "manual": m["manual"] or None,
                "fragmentos": [f for f in m["fragmentos"].split(",") if f], "fecha": m["fecha"],
                "similitud": similitud}

    def obtener(self, id):
        datos = self.vs.get(ids=[id], include=["documents", "metadatas"])
        if not datos["ids"]:
            return None
        return self._recuerdo(id, datos["documents"][0], datos["metadatas"][0])

    def listar(self):
        datos = self.vs.get(include=["documents", "metadatas"])
        recuerdos = [self._recuerdo(i, t, m) for i, t, m in zip(datos["ids"], datos["documents"], datos["metadatas"])]
        return sorted(recuerdos, key=lambda r: r["fecha"], reverse=True)

    def buscar(self, vector):
        """Consultas validadas parecidas (similitud coseno >= umbral), de la más a la menos parecida."""
        cantidad = len(self)
        if not cantidad:
            return []
        resultados = self.vs.similarity_search_by_vector_with_relevance_scores(vector, k=min(self.maximo, cantidad))
        recuerdos = [self._recuerdo(d.id, d.page_content, d.metadata, round(1 - dist, 4)) for d, dist in resultados]
        return [r for r in recuerdos if r["similitud"] >= self.umbral]


def obtener_memoria(nombre=COLECCION_MEMORIA, persistir=True):
    # Las preguntas se guardan con el mismo tipo de embedding que las consultas (RETRIEVAL_QUERY),
    # porque acá se compara una pregunta con otra pregunta, no con un fragmento de manual
    vs = Chroma(collection_name=nombre, embedding_function=get_embeddings("RETRIEVAL_QUERY"),
                persist_directory=str(CHROMA_DIR) if persistir else None,
                collection_metadata={"hnsw:space": "cosine"})
    return Memoria(vs)
