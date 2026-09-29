"""Cadena RAG: decide en qué manual buscar, recuerda consultas validadas, recupera los fragmentos y responde."""

import re

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from .config import TOP_K
from .recuperacion import formatear_contexto, sin_acentos

MAX_HISTORIAL = 4  # mensajes anteriores que se le pasan al modelo
PALABRAS_SEGUIMIENTO = 5  # una pregunta así de corta se toma como continuación de la anterior
CITA = re.compile(r"\s*\[\d+\]")  # citas [n] de una respuesta

SYSTEM_PROMPT = """Sos un asistente para consultar manuales técnicos de máquinas \
industriales. Respondés en español, de forma clara y práctica, a operarios y técnicos.

Reglas:
1. Usá EXCLUSIVAMENTE la información del CONTEXTO (fragmentos de manuales). No uses \
conocimiento externo ni inventes valores.
2. Citá la fuente de cada dato con su número entre corchetes, por ejemplo [1] o [2][3].
3. Si el contexto no contiene la respuesta, decí: "No encontré esa información en los \
manuales cargados" y sugerí consultar al fabricante o al supervisor.
4. No mezcles datos de máquinas distintas.
5. Para procedimientos, usá pasos numerados. Mantené las unidades (bar, N·m, horas, °C).
6. Si la tarea implica intervenir la máquina y el contexto menciona medidas de seguridad \
(LOTO, despresurizar, EPP), recordalas al inicio.
7. Sé breve. No uses LaTeX ni fórmulas: escribí las cuentas en texto plano.
8. Las CONSULTAS VALIDADAS son preguntas parecidas que un técnico ya marcó como bien \
respondidas. Usalas como guía de qué información sirve y cómo responder, pero tomá los datos \
y las citas solo del CONTEXTO.

===== CONSULTAS VALIDADAS =====
{validadas}
===== CONTEXTO =====
{context}
===================="""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


# --- Mensajes de cortesía ("ok", "gracias", "hola"...): se responden sin buscar ni llamar al LLM ---
PALABRAS_CORTESIA = {
    "gracias": """gracias grasias muchas mil muchisimas genio crack capo""",
    "saludo": """hola buenas buen buenos dia dias tardes noches que tal como estas hey""",
    "despedida": """chau chao adios hasta luego pronto manana nos vemos saludos""",
    "acuerdo": """ok oka okey okay dale bueno bien perfecto listo joya genial excelente barbaro buenisimo
                  entendido entiendo claro vale si ya de acuerdo super re muy todo ahi va copado""",
}
RESPUESTAS_CORTESIA = {
    "gracias": "¡De nada! Si tenés otra consulta sobre los manuales, preguntame.",
    "saludo": "¡Hola! ¿En qué te puedo ayudar? Podés preguntarme sobre mantenimiento, fallas o "
              "procedimientos de las máquinas de los manuales cargados.",
    "despedida": "¡Hasta luego! Cuando necesites consultar un manual, acá estoy.",
    "acuerdo": "Perfecto. Si tenés otra consulta sobre los manuales, preguntame.",
}
MAX_PALABRAS_CORTESIA = 6


def _normalizar(palabra):
    return re.sub(r"(.)\1+", r"\1", palabra)  # "graciasss" -> "gracias", "okk" -> "ok"


_TIPO_PALABRA = {_normalizar(p): tipo for tipo, texto in PALABRAS_CORTESIA.items() for p in texto.split()}


def respuesta_cortesia(texto):
    """Si el mensaje es solo cortesía (sin ninguna pregunta técnica), devuelve una respuesta fija; si no, None."""
    palabras = [_normalizar(p) for p in re.findall(r"[a-zñ]+", sin_acentos(texto.lower()))]
    if not palabras or len(palabras) > MAX_PALABRAS_CORTESIA or any(p not in _TIPO_PALABRA for p in palabras):
        return None
    tipos = {_TIPO_PALABRA[p] for p in palabras}
    for tipo in ("gracias", "despedida", "saludo"):  # "ok, gracias" -> se responde al agradecimiento
        if tipo in tipos:
            return RESPUESTAS_CORTESIA[tipo]
    return RESPUESTAS_CORTESIA["acuerdo"]


def sin_cortesias(historial):
    """Quita del historial los mensajes de cortesía y sus respuestas, para que no se tomen como contexto."""
    resultado, saltear = [], False
    for m in historial:
        if m["role"] == "user":
            saltear = respuesta_cortesia(m["content"]) is not None
        if not saltear:
            resultado.append(m)
    return resultado


def a_mensajes(historial):
    """Convierte [{'role': 'user'|'assistant', 'content': ...}] en mensajes de LangChain."""
    return [(HumanMessage if m["role"] == "user" else AIMessage)(content=m["content"])
            for m in historial[-MAX_HISTORIAL:]]


def cadena_respuesta(llm):
    return prompt | llm | StrOutputParser()


def preparar_consulta(pregunta, historial, recuperador, manual_elegido=None):
    """Decide en qué manual buscar y qué texto buscar, sin llamar al LLM.

    origen: "elegido" (lo fijó el usuario en la interfaz), "detectado" (la pregunta nombra
    la máquina), "contexto" (sale de la pregunta anterior) o None (se busca en todos).
    """
    anteriores = [m["content"] for m in historial if m["role"] == "user"]
    manual, origen = manual_elegido, "elegido" if manual_elegido else None
    detectado = recuperador.detectar_manual(pregunta)
    if not manual and detectado:
        manual, origen = detectado, "detectado"

    consulta = pregunta
    # Pregunta de seguimiento ("¿y cuántas veces puedo rearmarlo?"): se le suma la anterior
    # para que tenga palabras que buscar, y se mantiene el manual de la conversación.
    if anteriores and (not detectado or len(pregunta.split()) <= PALABRAS_SEGUIMIENTO):
        consulta = f"{anteriores[-1]} {pregunta}"
        if not manual:
            manual = recuperador.detectar_manual(anteriores[-1])
            origen = "contexto" if manual else None
    return {"consulta": consulta, "manual": manual, "origen": origen}


def recordar(plan, vector, memoria):
    """Busca consultas validadas parecidas. Si ninguna regla eligió el manual, usa el de la más parecida.

    Solo se usan recuerdos del mismo manual (o sin manual), para no mezclar máquinas.
    """
    recuerdos = memoria.buscar(vector) if memoria is not None else []
    if not plan["manual"] and recuerdos and recuerdos[0]["manual"]:
        plan = {**plan, "manual": recuerdos[0]["manual"], "origen": "aprendido"}
    if plan["manual"]:
        recuerdos = [r for r in recuerdos if r["manual"] in (plan["manual"], None)]
    return plan, recuerdos


def formatear_validadas(recuerdos):
    """Bloque de consultas validadas para el prompt. Se quitan sus citas [n], que eran de otro contexto."""
    if not recuerdos:
        return "(ninguna)"
    return "\n\n".join(f"Pregunta: {r['consulta']}\nRespuesta validada: {re.sub(CITA, '', r['respuesta'])}"
                       for r in recuerdos)


def recuperar(pregunta, historial, recuperador, memoria=None, k=TOP_K, manual_elegido=None):
    """Todo lo que pasa antes del LLM: plan, recuerdos de la memoria y fragmentos recuperados."""
    plan = preparar_consulta(pregunta, historial, recuperador, manual_elegido)
    vector = recuperador.embeber(plan["consulta"])  # un solo embedding para la memoria y los manuales
    plan, recuerdos = recordar(plan, vector, memoria)
    fuentes = recuperador.buscar(plan["consulta"], k=k, modelo=plan["manual"], vector=vector, recuerdos=recuerdos)
    return {"plan": plan, "recuerdos": recuerdos, "fuentes": fuentes}


def crear_cadena_rag(recuperador, llm, memoria=None, k=TOP_K):
    """Cadena completa. Entrada: {"input", "historial"}. Agrega "plan", "recuerdos", "fuentes" y "respuesta"."""
    return (
        RunnableLambda(lambda x: {**x, **recuperar(x["input"], x["historial"], recuperador, memoria, k)})
        | RunnablePassthrough.assign(
            context=lambda x: formatear_contexto(x["fuentes"]),
            validadas=lambda x: formatear_validadas(x["recuerdos"]),
            chat_history=lambda x: a_mensajes(x["historial"]))
        | RunnablePassthrough.assign(respuesta=cadena_respuesta(llm))
    )
