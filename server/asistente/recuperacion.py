"""Búsqueda híbrida (embeddings + BM25 + memoria, fusionadas con RRF) y detección del manual."""

import re
import unicodedata

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

RRF_K = 60  # constante usual de Reciprocal Rank Fusion

STOPWORDS = set("""
a al algo ante como con contra cual cuales cuando de del desde donde durante e el ella
ellos en entre era es esa ese eso esta este esto hay la las le les lo los mas me mi muy
no o para pero por que se sea ser si sin sobre su sus tambien te tiene un una uno unos
y ya hace hacer debo tengo cada cuanto cuantos cuanta cuantas qué cómo puede
""".split())


def sin_acentos(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def tokenizar(texto):
    """Tokenizador para BM25: minúsculas, sin acentos y sin stopwords.

    Conserva los códigos ("al-205") y además agrega sus partes ("al", "205"),
    y los números con punto de miles también se agregan sin él ("4.000" -> "4000").
    """
    tokens = []
    for tok in re.findall(r"[a-z0-9]+(?:[-.,][a-z0-9]+)*", sin_acentos(texto.lower())):
        if tok in STOPWORDS:
            continue
        tokens.append(tok)
        if "-" in tok:
            tokens.extend(p for p in tok.split("-") if p)
        if re.fullmatch(r"\d+([.,]\d+)+", tok):
            tokens.append(re.sub(r"[.,]", "", tok))
    return tokens


class RecuperadorHibrido:
    def __init__(self, vectorstore, candidatos=12):
        self.vs = vectorstore
        self.candidatos = candidatos  # resultados que aporta cada buscador antes de fusionar
        # BM25 se arma con los mismos chunks guardados en Chroma
        datos = vectorstore.get(include=["documents", "metadatas"])
        self.docs = [Document(page_content=t, metadata=m, id=i)
                     for i, t, m in zip(datos["ids"], datos["documents"], datos["metadatas"])]
        self.por_id = {d.id: d for d in self.docs}
        self.bm25 = BM25Okapi([tokenizar(d.page_content) for d in self.docs])
        self.patrones = self._patrones_por_manual()

    @property
    def modelos(self):
        return sorted({d.metadata["modelo"] for d in self.docs})

    # --- Detección del manual (sin usar el LLM) ---
    def _patrones_por_manual(self):
        """Para cada manual, expresiones regulares con su código de modelo y sus alias."""
        palabras = {}
        for d in self.docs:
            m = d.metadata
            palabras.setdefault(m["modelo"], {m["modelo"]}).update(
                a.strip() for a in m.get("alias", "").split(",") if a.strip())
        patrones = {}
        for modelo, claves in palabras.items():
            lista = []
            for clave in claves:
                clave = sin_acentos(clave.lower())
                for v in {clave, clave.replace("-", ""), clave.replace("-", " ")}:  # CT-75, CT75, CT 75
                    lista.append(re.compile(rf"\b{re.escape(v)}(es|s)?\b"))  # admite plural
            patrones[modelo] = lista
        return patrones

    def detectar_manual(self, texto):
        """Devuelve el manual que nombra el texto, o None si no nombra ninguno o nombra varios."""
        texto = sin_acentos(texto.lower())
        encontrados = [modelo for modelo, pats in self.patrones.items() if any(p.search(texto) for p in pats)]
        return encontrados[0] if len(encontrados) == 1 else None

    # --- Búsqueda ---
    def embeber(self, texto):
        """Embedding de la consulta: se calcula una vez y se usa para los manuales y para la memoria."""
        return self.vs.embeddings.embed_query(texto)

    def buscar_vectorial(self, consulta, k, modelo=None, vector=None):
        filtro = {"modelo": modelo} if modelo else None
        vector = vector if vector is not None else self.embeber(consulta)
        resultados = self.vs.similarity_search_by_vector_with_relevance_scores(vector, k=k, filter=filtro)
        return [(d, round(1 - dist, 4)) for d, dist in resultados]  # distancia coseno -> similitud

    def buscar_bm25(self, consulta, k, modelo=None):
        puntajes = self.bm25.get_scores(tokenizar(consulta))
        orden = sorted(range(len(self.docs)), key=lambda i: puntajes[i], reverse=True)
        resultado = []
        for i in orden:
            if puntajes[i] <= 0 or len(resultado) == k:
                break
            if modelo and self.docs[i].metadata["modelo"] != modelo:
                continue
            resultado.append((self.docs[i], round(float(puntajes[i]), 4)))
        return resultado

    def buscar_aprendidos(self, recuerdos, modelo=None):
        """Fragmentos que citaron las respuestas validadas parecidas, puntuados con la similitud de cada recuerdo."""
        resultado, vistos = [], set()
        for r in recuerdos:
            for fid in r["fragmentos"]:
                doc = self.por_id.get(fid)  # si el manual se reindexó, el fragmento puede no existir
                if doc and fid not in vistos and (not modelo or doc.metadata["modelo"] == modelo):
                    vistos.add(fid)
                    resultado.append((doc, r["similitud"]))
        return resultado

    def buscar(self, consulta, k=5, modelo=None, modo="hibrido", vector=None, recuerdos=()):
        """Devuelve los k chunks más relevantes. modo: "hibrido", "vectorial" o "bm25".

        recuerdos: consultas validadas parecidas (memoria); sus fragmentos entran como una lista más de RRF.
        """
        vect = self.buscar_vectorial(consulta, self.candidatos, modelo, vector) if modo != "bm25" else []
        lex = self.buscar_bm25(consulta, self.candidatos, modelo) if modo != "vectorial" else []
        mem = self.buscar_aprendidos(recuerdos, modelo)

        # RRF: cada lista suma 1 / (60 + posición) a los chunks que encontró
        fusion = {}
        for nombre, lista in (("vectorial", vect), ("bm25", lex), ("memoria", mem)):
            for posicion, (doc, puntaje) in enumerate(lista, start=1):
                item = fusion.setdefault(doc.id, {"doc": doc, "rrf": 0.0})
                item["rrf"] += 1 / (RRF_K + posicion)
                item[f"score_{nombre}"] = puntaje

        mejores = sorted(fusion.values(), key=lambda x: x["rrf"], reverse=True)[:k]
        resultado = []
        for item in mejores:
            d = item.pop("doc")
            resultado.append(Document(page_content=d.page_content, metadata={**d.metadata, **item}, id=d.id))
        return resultado


def formatear_contexto(docs):
    """Arma el bloque de contexto numerado que va en el prompt."""
    bloques = []
    for i, d in enumerate(docs, start=1):
        m = d.metadata
        bloques.append(f"[{i}] Fuente: {m['archivo']} | {m['modelo']} | {m['seccion']}\n{d.page_content}")
    return "\n\n".join(bloques)
