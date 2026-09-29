# MantenIA - Consulta de manuales técnicos (TP N°2)

Sistema RAG para consultar manuales de máquinas industriales en lenguaje natural, hecho con LangChain, Gemini y Chroma. Para cada pregunta decide en qué manual buscar, recupera los fragmentos relevantes (embeddings + BM25) y responde citando la fuente.

El entregable principal es el notebook `server/TP2_MantenIA.ipynb`. La aplicación web (FastAPI + React) usa el mismo código.

## Estructura

```
React/
├── server/
│   ├── TP2_MantenIA.ipynb   ← notebook del TP
│   ├── main.py              ← API FastAPI
│   ├── asistente/           ← mismo código que el notebook
│   │   ├── config.py        ← parámetros y modelos de Gemini
│   │   ├── ingesta.py       ← carga, chunking e índice Chroma
│   │   ├── recuperacion.py  ← búsqueda híbrida y detección del manual
│   │   ├── rag.py           ← cadena RAG
│   │   └── evaluacion.py    ← casos de prueba y métricas
│   └── data/manuales/       ← manuales (.md)
└── client/                  ← interfaz web (React + Vite)
```

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

Abrir `server/TP2_MantenIA.ipynb` con el kernel de `server/.venv` y ejecutar todo, o desde `server/`:

```powershell
.venv\Scripts\python -m nbconvert --to notebook --execute --inplace TP2_MantenIA.ipynb
```

Hace 17 llamadas al LLM (3 ejemplos y 14 casos de prueba). La primera vez también construye el índice en `chroma_db/`.

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

Abrir http://localhost:5173. También se puede usar **F5 → "MantenIA: server + client"** en VS Code.
