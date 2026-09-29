"""Casos de prueba y métricas de evaluación.

- Recuperación: Hit@k (algún chunk del top-k tiene la respuesta) y MRR (1 / posición del
  primer chunk correcto, promediado).
- Detección de manual: si el sistema eligió el manual correcto o buscó en todos.
- Respuesta: si la respuesta contiene el dato esperado (o, fuera de dominio, si admite que no sabe).
"""

import time
import unicodedata
from dataclasses import dataclass

import pandas as pd


@dataclass
class Caso:
    pregunta: str
    modelo: str | None  # manual donde está la respuesta (None = fuera de dominio)
    evidencia: str      # texto que tiene que estar en el chunk correcto
    respuesta: str      # dato que tiene que aparecer en la respuesta
    tipo: str           # "código", "semántica" o "fuera de dominio"


CASOS = [
    Caso("¿Qué significa la alarma A01 del compresor?", "CT-75", "A01", "temperatura", "código"),
    Caso("¿Cada cuántas horas hay que cambiar el aceite del compresor?", "CT-75", "4.000 horas", "4.000", "semántica"),
    Caso("¿Qué aceite usa el CT-75 y cuántos litros lleva?", "CT-75", "LubriScrew", "38", "código"),
    Caso("Tengo la alarma AL-205 en el torno", "TC-420", "AL-205", "40 bar", "código"),
    Caso("El torno se queda sin fuerza para sujetar la pieza en el plato, parece falta de aceite en el sistema",
         "TC-420", "presión hidráulica baja", "hidráulic", "semántica"),
    Caso("¿Cómo caliento el husillo si la máquina estuvo parada todo el fin de semana?", "TC-420", "1.000 rpm", "1.000", "semántica"),
    Caso("¿Qué concentración tiene que tener el refrigerante del torno?", "TC-420", "5 % a 8 %", "8", "semántica"),
    Caso("La inyectora marca E-17, ¿qué hago?", "IP-250", "termocupla", "termocupla", "código"),
    Caso("¿A qué temperatura se inyecta el ABS?", "IP-250", "ABS", "210", "código"),
    Caso("¿Cada cuánto se engrasan los rodamientos de la cinta transportadora?", "CB-1200", "NLGI 2", "500", "semántica"),
    Caso("¿Qué torque llevan los bulones M16 de la cinta?", "CB-1200", "M16", "210", "código"),
    Caso("La banda resbala sobre el tambor que la mueve, ¿qué puede ser?", "CB-1200", "patina", "tensi", "semántica"),
    Caso("Un compañero se fue a su casa y dejó su candado puesto en la máquina, ¿quién lo puede sacar?",
         "PRO-SEG-001", "Candado olvidado", "jefe de mantenimiento", "semántica"),
    Caso("¿Cuál es el torque de la tapa de cilindros del motor diésel XR-9?", None, "", "no encontr", "fuera de dominio"),
]


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def es_relevante(doc, caso):
    return doc.metadata["modelo"] == caso.modelo and normalizar(caso.evidencia) in normalizar(doc.page_content)


def evaluar_recuperacion(recuperador, k, modos=("vectorial", "bm25", "hibrido")):
    """Una fila por (pregunta, modo) con la posición del primer chunk relevante."""
    filas = []
    for caso in CASOS:
        if caso.modelo is None:
            continue
        for modo in modos:
            docs = recuperador.buscar(caso.pregunta, k=k, modo=modo)
            posicion = next((i for i, d in enumerate(docs, start=1) if es_relevante(d, caso)), None)
            filas.append({"pregunta": caso.pregunta, "tipo": caso.tipo, "modo": modo, "posicion": posicion,
                          "hit": posicion is not None, "rr": 1 / posicion if posicion else 0.0})
    return pd.DataFrame(filas)


def resumen_recuperacion(df):
    """Hit@k y MRR por modo, en total y por tipo de pregunta."""
    total = df.groupby("modo").agg(hit_at_k=("hit", "mean"), mrr=("rr", "mean"))
    por_tipo = df.pivot_table(index="modo", columns="tipo", values="hit", aggfunc="mean")
    por_tipo.columns = [f"hit@k ({c})" for c in por_tipo.columns]
    return total.join(por_tipo).round(3).loc[["vectorial", "bm25", "hibrido"]]


def evaluar_deteccion(recuperador):
    """correcto = eligió el manual de la respuesta; todos = no filtró; incorrecto = eligió otro."""
    filas = []
    for caso in CASOS:
        detectado = recuperador.detectar_manual(caso.pregunta)
        if detectado is None:
            resultado = "todos"
        else:
            resultado = "correcto" if detectado == caso.modelo else "incorrecto"
        filas.append({"pregunta": caso.pregunta, "esperado": caso.modelo or "(ninguno)",
                      "detectado": detectado or "(todos)", "resultado": resultado})
    return pd.DataFrame(filas)


def evaluar_respuestas(cadena_rag, pausa=0):
    """Corre la cadena RAG con cada caso y verifica la respuesta.

    pausa: segundos entre preguntas, por el límite de pedidos por minuto del plan gratuito.
    """
    filas = []
    for caso in CASOS:
        inicio = time.perf_counter()
        salida = cadena_rag.invoke({"input": caso.pregunta, "historial": []})
        segundos = time.perf_counter() - inicio
        correcta = normalizar(caso.respuesta) in normalizar(salida["respuesta"])
        filas.append({"pregunta": caso.pregunta, "tipo": caso.tipo, "correcta": correcta,
                      "segundos": round(segundos, 1), "respuesta": salida["respuesta"]})
        time.sleep(pausa)
    return pd.DataFrame(filas)
