"""Configuración: rutas, parámetros y modelos de Gemini (LLM y embeddings)."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

BASE_DIR = Path(__file__).resolve().parent.parent
MANUALES_DIR = BASE_DIR / "data" / "manuales"
CHROMA_DIR = BASE_DIR / "chroma_db"
load_dotenv(BASE_DIR / ".env")
logging.getLogger("google_genai.models").setLevel(logging.ERROR)  # oculta un aviso interno del SDK de Gemini

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
TOP_K = int(os.getenv("TOP_K", "4"))  # fragmentos que se envían al modelo
COLLECTION_NAME = "manuales"


def get_llm():
    return ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=TEMPERATURE)


def get_embeddings():
    return GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
