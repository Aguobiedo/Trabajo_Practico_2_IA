"""Casos de prueba y métricas de evaluación.

- Recuperación: Hit@k (algún chunk del top-k tiene la respuesta) y MRR (1 / posición del
  primer chunk correcto, promediado).
- Detección de manual: si el sistema eligió el manual correcto o buscó en todos.
- Respuesta: si la respuesta contiene el dato esperado (o, fuera de dominio, si admite que no sabe).
- Aprendizaje: detección del manual y recuperación antes y después de validar consultas parecidas.
"""

import time
import unicodedata
from dataclasses import dataclass

import pandas as pd

from .rag import preparar_consulta, recordar


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

# Consultas que un técnico ya hizo antes con otras palabras y validó con 👍 (se usan para entrenar la memoria)
VALIDADAS = [
    Caso("¿Qué temperatura de inyección lleva el ABS?", "IP-250", "ABS", "210", "validada"),
    Caso("La banda patina en el tambor motriz, ¿qué reviso?", "CB-1200", "patina", "tensi", "validada"),
    Caso("La máquina estuvo parada tres días, ¿cómo hago el calentamiento del husillo?", "TC-420", "1.000 rpm",
         "1.000", "validada"),
    Caso("Al torno le falta fuerza en el plato para agarrar la pieza, ¿qué puede ser?", "TC-420",
         "presión hidráulica baja", "hidráulic", "validada"),
    Caso("¿Cada cuánto hay que engrasar los rodamientos de la cinta?", "CB-1200", "NLGI 2", "500", "validada"),
    Caso("Un operario se fue y dejó su candado colocado, ¿quién puede retirarlo?", "PRO-SEG-001", "Candado olvidado",
         "jefe de mantenimiento", "validada"),
    Caso("¿Cuántos litros de aceite lleva el compresor y de qué tipo?", "CT-75", "LubriScrew", "38", "validada"),
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


def evaluar_respuestas(cadena_rag, pausa=0, casos=CASOS):
    """Corre la cadena RAG con cada caso y verifica la respuesta.

    pausa: segundos entre preguntas, por el límite de pedidos por minuto del plan gratuito.
    """
    filas = []
    for caso in casos:
        inicio = time.perf_counter()
        salida = cadena_rag.invoke({"input": caso.pregunta, "historial": []})
        segundos = time.perf_counter() - inicio
        correcta = normalizar(caso.respuesta) in normalizar(salida["respuesta"])
        filas.append({"pregunta": caso.pregunta, "tipo": caso.tipo, "correcta": correcta,
                      "segundos": round(segundos, 1), "recuerdos": len(salida["recuerdos"]),
                      "respuesta": salida["respuesta"]})
        time.sleep(pausa)
    return pd.DataFrame(filas)


# --- Aprendizaje ---
def entrenar_memoria(cadena_rag, memoria, pausa=0, casos=VALIDADAS):
    """Simula al técnico: corre cada consulta y la valida (👍) solo si la respuesta tiene el dato correcto."""
    filas = []
    for i, caso in enumerate(casos, start=1):
        salida = cadena_rag.invoke({"input": caso.pregunta, "historial": []})
        validada = normalizar(caso.respuesta) in normalizar(salida["respuesta"])
        recuerdo = None
        if validada:
            fuentes = [{"id": d.id, "modelo": d.metadata["modelo"]} for d in salida["fuentes"]]
            recuerdo = memoria.aprender(f"validada-{i:02d}", salida["plan"]["consulta"], salida["respuesta"], fuentes)
        filas.append({"pregunta": caso.pregunta, "validada": validada,
                      "manual aprendido": recuerdo["manual"] if recuerdo else None,
                      "fragmentos citados": ", ".join(recuerdo["fragmentos"]) if recuerdo else ""})
        time.sleep(pausa)
    return pd.DataFrame(filas)


def _resultado_manual(manual, esperado):
    if manual is None:
        return "todos"
    return "correcto" if manual == esperado else "incorrecto"


def evaluar_memoria(recuperador, memoria, k):
    """Para cada caso: manual elegido y posición del chunk correcto, sin y con la memoria.

    La recuperación se compara sin filtro por manual, igual que en evaluar_recuperacion.
    """
    filas = []
    for caso in CASOS:
        plan = preparar_consulta(caso.pregunta, [], recuperador)
        vector = recuperador.embeber(plan["consulta"])
        plan_con, recuerdos = recordar(plan, vector, memoria)
        posiciones = []
        for rec in ([], recuerdos):
            docs = recuperador.buscar(caso.pregunta, k=k, vector=vector, recuerdos=rec)
            posiciones.append(next((i for i, d in enumerate(docs, start=1) if es_relevante(d, caso)), None))
        filas.append({
            "pregunta": caso.pregunta, "tipo": caso.tipo, "esperado": caso.modelo or "(ninguno)",
            "recuerdos": len(recuerdos), "similitud": max((r["similitud"] for r in recuerdos), default=None),
            "manual sin memoria": _resultado_manual(plan["manual"], caso.modelo),
            "manual con memoria": _resultado_manual(plan_con["manual"], caso.modelo),
            "posición sin memoria": posiciones[0], "posición con memoria": posiciones[1],
        })
    return pd.DataFrame(filas)


def resumen_memoria(df):
    """Detección del manual y Hit@k / MRR (sobre los casos con respuesta en los manuales), sin y con memoria."""
    con_respuesta = df[df["esperado"] != "(ninguno)"]
    filas = {}
    for cuando in ("sin memoria", "con memoria"):
        conteo = df[f"manual {cuando}"].value_counts()
        pos = con_respuesta[f"posición {cuando}"]
        filas[cuando] = {"manual correcto": conteo.get("correcto", 0), "todos": conteo.get("todos", 0),
                         "manual incorrecto": conteo.get("incorrecto", 0), "hit@k": round(pos.notna().mean(), 3),
                         "mrr": round((1 / pos).fillna(0).mean(), 3)}
    return pd.DataFrame(filas).T
