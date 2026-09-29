"""Cadena RAG: decide en qué manual buscar, recupera los fragmentos y genera la respuesta."""

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from .config import TOP_K
from .recuperacion import formatear_contexto

MAX_HISTORIAL = 4  # mensajes anteriores que se le pasan al modelo
PALABRAS_SEGUIMIENTO = 5  # una pregunta así de corta se toma como continuación de la anterior

SYSTEM_PROMPT = """Sos MantenIA, un asistente para consultar manuales técnicos de máquinas \
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

===== CONTEXTO =====
{context}
===================="""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


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


def crear_cadena_rag(recuperador, llm, k=TOP_K):
    """Cadena completa. Entrada: {"input", "historial"}. Agrega "plan", "fuentes" y "respuesta"."""
    return (
        RunnablePassthrough.assign(plan=RunnableLambda(
            lambda x: preparar_consulta(x["input"], x["historial"], recuperador)))
        | RunnablePassthrough.assign(fuentes=RunnableLambda(
            lambda x: recuperador.buscar(x["plan"]["consulta"], k=k, modelo=x["plan"]["manual"])))
        | RunnablePassthrough.assign(
            context=lambda x: formatear_contexto(x["fuentes"]),
            chat_history=lambda x: a_mensajes(x["historial"]))
        | RunnablePassthrough.assign(respuesta=cadena_respuesta(llm))
    )
