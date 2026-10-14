# Asistente de Mantenimiento - Consulta de manuales técnicos (TP N°2)

Sistema RAG para consultar manuales de máquinas industriales en lenguaje natural, hecho con LangChain, Gemini y Chroma. Para cada pregunta decide en qué manual buscar, recupera los fragmentos relevantes (embeddings + BM25) y responde citando la fuente. Además aprende de las conversaciones: las respuestas que el usuario marca con 👍 se recuerdan y se usan en consultas parecidas.

El entregable principal es el notebook `server/TP2_Asistente.ipynb`. La aplicación web (FastAPI + React) usa el mismo código y se ejecuta con Docker.

## Datos del trabajo

- **Universidad:** Universidad Tecnológica Nacional - Facultad Regional Rosario
- **Materia:** Inteligencia Artificial
- **Trabajo:** Trabajo Práctico N°2 - Sistemas Inteligentes con RAG o Agentes
- **Docentes:** Ing. Laura Aquili e Ing. Gerónimo Forconi

**Grupo 15**

| Legajo | Apellido y nombre |
|---|---|
| 47953 | Rodríguez, Guido |
| 48127 | Nardi, Matías Antonio |
| 47793 | Obiedo, Agustín |
| 47779 | Baigorria, Lotar Karlos |
| 47901 | Sinópoli, Martina |

## Estructura

```
Trabajo_Practico_2_IA/
├── compose.yaml             ← los tres contenedores: server, client y redis
├── Makefile                 ← atajos opcionales para Docker Compose
├── server/
│   ├── TP2_Asistente.ipynb  ← notebook del TP
│   ├── main.py              ← API FastAPI
│   ├── Dockerfile
│   ├── .env.example         ← plantilla de configuración (copiar como .env)
│   ├── asistente/           ← mismo código que el notebook
│   │   ├── config.py        ← parámetros y modelos de Gemini
│   │   ├── ingesta.py       ← carga, chunking e índice Chroma
│   │   ├── recuperacion.py  ← búsqueda híbrida y detección del manual
│   │   ├── memoria.py       ← aprendizaje: consultas validadas con 👍
│   │   ├── rag.py           ← cadena RAG
│   │   └── evaluacion.py    ← casos de prueba y métricas
│   └── data/manuales/       ← manuales (.md)
└── client/                  ← interfaz web (React + Vite)
    ├── Dockerfile
    └── nginx.conf           ← sirve la web y reenvía /api al server
```

## Aprendizaje

El historial de la conversación activa se guarda en Redis durante 30 días por defecto y se recupera al volver a abrir la aplicación en el mismo navegador. «Nueva» inicia otra conversación; no borra las anteriores. El historial sirve como contexto para las siguientes respuestas. Además, cuando el usuario marca una respuesta con 👍, se guardan en la colección `memoria` de Chroma (`server/chroma_db/`) la pregunta, la respuesta y los fragmentos que citó. Ante una pregunta parecida (similitud ≥ `UMBRAL_MEMORIA`, 0,88 por defecto), el sistema:

1. usa el manual de esa consulta si la pregunta no nombra ninguna máquina;
2. suma sus fragmentos a la búsqueda híbrida como una lista más de RRF;
3. le pasa la respuesta validada al LLM como ejemplo.

👎 no se aprende, y si la consulta estaba aprendida la quita. En la página **Aprendizaje** se ve lo aprendido y se puede olvidar cada consulta.

## Ejecución con Docker

La aplicación web se ejecuta con Docker Compose en tres contenedores:

| Servicio | Qué es | Dirección |
|---|---|---|
| `client` | Interfaz React servida por Nginx, que reenvía `/api` al server | http://localhost:5173 |
| `server` | API FastAPI | http://localhost:8000 |
| `redis` | Historial de conversaciones | solo dentro de Docker |

### Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/), que ya incluye Docker Compose. En Windows usa WSL 2: si no está instalado, Docker Desktop ofrece instalarlo al abrirse por primera vez (o se instala con `wsl --install` en una terminal de administrador) y hay que reiniciar el equipo.
- Una API key de Gemini: https://aistudio.google.com/apikey

### Primera vez

Desde la carpeta raíz del proyecto:

```powershell
copy server\.env.example server\.env
```

Completar `GOOGLE_API_KEY` en `server/.env`. Con Docker Desktop abierto y el motor en marcha ("Engine running"):

```powershell
docker compose up --build -d
```

Abrir http://localhost:5173. La primera vez tarda unos minutos: se construyen las imágenes y el server arma el índice de Chroma con los manuales de `server/data/manuales/`. Mientras tanto, la barra lateral muestra que el server todavía no está listo y reintenta sola.

### Comandos

Todos desde la carpeta raíz:

| Acción | Comando | Atajo con Make |
|---|---|---|
| Construir y levantar | `docker compose up --build -d` | `make up` |
| Estado de los contenedores | `docker compose ps` | `make status` |
| Logs en vivo | `docker compose logs -f` | `make logs` |
| Reiniciar los servicios | `docker compose restart` | `make restart` |
| Detener y eliminar los contenedores | `docker compose down` | `make down` |
| Levantar solo Redis | `docker compose up -d redis` | `make redis` |

Los atajos necesitan GNU Make, que es opcional. En Windows, si está instalado como MinGW, el comando es `mingw32-make` en lugar de `make`.

Después de cambiar el código o `requirements.txt`, volver a ejecutar `docker compose up --build -d` para reconstruir las imágenes. Si solo cambió `server/.env`, alcanza con `docker compose up -d`.

### Datos

- El índice y lo aprendido (Chroma) se guardan en el volumen `chroma_data`, y el historial de conversaciones (Redis) en `redis_data`.
- Los manuales están en `server/data/manuales/`, que es una carpeta del equipo compartida con el contenedor.
- `docker compose down` conserva todo lo anterior. `docker compose down -v` también borra los dos volúmenes: se pierden el índice, lo aprendido y los historiales, y el índice se reconstruye en el siguiente arranque.
- Redis conserva cada historial por 30 días, configurable con `CONVERSATION_TTL_SECONDS` en `server/.env`.

### Problemas frecuentes

- **`docker` no se reconoce como comando**: abrir una terminal nueva después de instalar Docker Desktop.
- **Error al conectar con el motor de Docker**: Docker Desktop no está abierto o todavía está iniciando.
- **Puerto 5173 u 8000 en uso**: cerrar el server o el client que estén corriendo fuera de Docker.
- **La barra lateral muestra "Falta GOOGLE_API_KEY"**: completar la clave en `server/.env` y ejecutar `docker compose up -d`.

## Uso de la aplicación

La barra lateral muestra el estado del server (modelo, manuales cargados y consultas aprendidas) y permite cambiar entre tres páginas.

**Consultas**

- Escribir la pregunta y enviar con Enter. La respuesta llega en streaming y cita los fragmentos de manual que usó.
- **Manual**: en "automático" el sistema detecta de qué máquina se habla; también se puede elegir un manual fijo.
- **k**: cantidad de fragmentos de manual que se envían al modelo (por defecto `TOP_K`, 4).
- 👍 guarda la respuesta como validada para usarla en consultas parecidas; 👎 la quita si estaba aprendida.
- **Nueva** inicia otra conversación. La anterior queda guardada en Redis.
- Mensajes como "ok" o "gracias" se responden con un texto fijo, sin llamar al modelo.

**Manuales**

Lista los manuales indexados, permite ver su contenido y agregar nuevos: archivos `.md`, `.txt`, `.pdf`, `.jpg`, `.jpeg` o `.png` de hasta 10 MB. Al subir uno se pueden indicar modelo, equipo y alias, que tienen prioridad sobre el encabezado del archivo. Se guarda como `.md` en `server/data/manuales/` y se indexa en el momento, sin reconstruir todo el índice.

- Los PDF se convierten a Markdown con MarkItDown. Si la conversión no produce títulos, todos sus fragmentos quedan en la sección "General". Un PDF escaneado, sin texto, no se puede leer.
- Las imágenes se convierten a Markdown con una descripción que genera Gemini (texto legible, piezas, etiquetas y valores), así que cada imagen subida hace una llamada a la API.

**Aprendizaje**

Muestra las consultas validadas con 👍 y permite olvidar cada una.

## Ejecución sin Docker (desarrollo)

Para modificar el código con recarga automática se pueden ejecutar el server y el client directamente. Requiere Python 3.10+ y Node.js. Redis se sigue levantando con Docker.

Instalación:

```powershell
cd server
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env      # y pegar la GOOGLE_API_KEY
cd ..\client
npm install
```

Iniciar Redis desde la raíz del proyecto:

```powershell
docker compose up -d redis
```

El server lee `REDIS_URL` de `server/.env` (por defecto `redis://localhost:6379/0`). Después, en dos terminales:

```powershell
# server
cd server
.venv\Scripts\python -m uvicorn main:app --port 8000

# client
cd client
npm run dev
```

Abrir http://localhost:5173. También se puede usar **F5 → "Asistente de Mantenimiento: server + client"** en VS Code.

Esta forma usa los mismos puertos que los contenedores, así que antes hay que detenerlos con `docker compose down` (y volver a levantar solo Redis). El índice queda en `server/chroma_db/`, separado del volumen que usa Docker.

## Notebook

Requiere la instalación de Python de la sección anterior; no necesita Docker ni Redis. Abrir `server/TP2_Asistente.ipynb` con el kernel de `server/.venv` y ejecutar todo, o desde `server/`:

```powershell
.venv\Scripts\python -m nbconvert --to notebook --execute --inplace TP2_Asistente.ipynb
```

Hace 31 llamadas al LLM (3 ejemplos, 14 casos de prueba y 14 de la evaluación del aprendizaje) y tarda unos 7 minutos. La primera vez también construye el índice en `chroma_db/`. La memoria que se usa en la evaluación es temporal, así que no modifica lo que aprendió la aplicación web.
