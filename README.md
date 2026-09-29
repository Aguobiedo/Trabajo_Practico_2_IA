# Asistente de Mantenimiento - Consulta de manuales técnicos (TP N°2)

Sistema RAG para consultar manuales de máquinas industriales en lenguaje natural, hecho con LangChain, Gemini y Chroma. Para cada pregunta decide en qué manual buscar, recupera los fragmentos relevantes (embeddings + BM25) y responde citando la fuente. Además aprende de las conversaciones: las respuestas que el usuario marca con 👍 se recuerdan y se usan en consultas parecidas.

El entregable principal es el notebook `server/TP2_Asistente.ipynb`. La aplicación web (FastAPI + React) usa el mismo código.

## Estructura

```
Trabajo_Practico_2_IA/
├── server/
│   ├── TP2_Asistente.ipynb   ← notebook del TP
│   ├── main.py              ← API FastAPI
│   ├── asistente/           ← mismo código que el notebook
│   │   ├── config.py        ← parámetros y modelos de Gemini
│   │   ├── ingesta.py       ← carga, chunking e índice Chroma
│   │   ├── recuperacion.py  ← búsqueda híbrida y detección del manual
│   │   ├── memoria.py       ← aprendizaje: consultas validadas con 👍
│   │   ├── rag.py           ← cadena RAG
│   │   └── evaluacion.py    ← casos de prueba y métricas
│   └── data/manuales/       ← manuales (.md)
└── client/                  ← interfaz web (React + Vite)
```

## Aprendizaje

Las conversaciones **no se guardan**: el historial vive en el navegador y se descarta con «Nueva». Lo que se guarda es lo aprendido. Cuando el usuario marca una respuesta con 👍, se guardan en la colección `memoria` de Chroma (`server/chroma_db/`) la pregunta, la respuesta y los fragmentos que citó. Ante una pregunta parecida (similitud ≥ `UMBRAL_MEMORIA`, 0,88 por defecto), el sistema:

1. usa el manual de esa consulta si la pregunta no nombra ninguna máquina;
2. suma sus fragmentos a la búsqueda híbrida como una lista más de RRF;
3. le pasa la respuesta validada al LLM como ejemplo.

👎 no se aprende, y si la consulta estaba aprendida la quita. En la página **Aprendizaje** se ve lo aprendido y se puede olvidar cada consulta.

## Instalación

```powershell
cd server
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env      # y pegar la GOOGLE_API_KEY
cd ..\client
npm install
```

## Notebook

Abrir `server/TP2_Asistente.ipynb` con el kernel de `server/.venv` y ejecutar todo, o desde `server/`:

```powershell
.venv\Scripts\python -m nbconvert --to notebook --execute --inplace TP2_Asistente.ipynb
```

Hace 31 llamadas al LLM (3 ejemplos, 14 casos de prueba y 14 de la evaluación del aprendizaje) y tarda unos 7 minutos. La primera vez también construye el índice en `chroma_db/`. La memoria que se usa en la evaluación es temporal, así que no modifica lo que aprendió la aplicación web.

## Aplicación web

Dos terminales:

```powershell
# server
cd server
.venv\Scripts\python -m uvicorn main:app --port 8000

# client
cd client
npm run dev
```

Abrir http://localhost:5173. También se puede usar **F5 → "Asistente de Mantenimiento: server + client"** en VS Code.

En la sección **Manuales** se pueden agregar manuales nuevos (.md, .txt o .pdf, hasta 10 MB). Se guardan como `.md` en `server/data/manuales/` y se indexan en el momento, sin reconstruir todo el índice. Los PDF se convierten a texto plano, así que no conservan las secciones: todos sus fragmentos quedan en la sección "General".
