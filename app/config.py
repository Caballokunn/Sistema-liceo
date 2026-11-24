import os

from dotenv import load_dotenv

load_dotenv()


def _req(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Falta la variable de entorno {name}")
    return value


# --- Base de datos (Supabase) ---
DATABASE_URL = _req("DB_URL")

# --- Seguridad de tu API ---
API_KEY = _req("API_KEY")
JWT_SECRET = _req("JWT_SECRET")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.environ.get("JWT_EXPIRATION_MINUTES", "60"))

# --- Embeddings (locales, gratis) ---
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")  # 384 dims

# --- LLM: lista ordenada de backends; se prueba el siguiente si uno falla ---
# Valores: "opencode", "openai"
LLM_BACKENDS = [b.strip() for b in os.environ.get("LLM_BACKENDS", "openai").split(",") if b.strip()]
LLM_TIMEOUT = float(os.environ.get("LLM_TIMEOUT", "120"))

# Backend "openai" (cualquier API compatible: OpenRouter, Groq, Gemini-compat, OpenAI...)
LLM_BASE_URL = os.environ.get("LLM_BASE_URL")
LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL")
