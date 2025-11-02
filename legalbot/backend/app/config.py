import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional
from functools import lru_cache
from urllib.parse import unquote_plus

# ----------------------------------------------------
# 🌍 Dynamic Environment Loader (local vs cloud)
# ----------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]

# Default environment mode: dev (can be overridden in .env)
APP_ENV = os.getenv("APP_ENV", "dev").lower()

# Select which .env file to load
if APP_ENV == "prod":
    ENV_PATH = BASE_DIR / ".env.gcp"   # ✅ For Google Cloud / Render / Prod
else:
    ENV_PATH = BASE_DIR / ".env.local" # ✅ For local testing

loaded = load_dotenv(dotenv_path=ENV_PATH, override=True)
print(f"🔍 Loading environment from: {ENV_PATH} (success={loaded}) — MODE: {APP_ENV.upper()}")

# ----------------------------------------------------
# ⚙️ Settings Class
# ----------------------------------------------------
class Settings:
    # ----------------------------
    # PostgreSQL (Main Backend DB)
    # ----------------------------
    POSTGRES_HOST: Optional[str] = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: Optional[str] = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: Optional[str] = os.getenv("POSTGRES_DB", "legalbot")
    POSTGRES_USER: Optional[str] = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: Optional[str] = unquote_plus(os.getenv("POSTGRES_PASSWORD", ""))

    # ----------------------------
    # RAG / Document Embeddings DB
    # ----------------------------
    RAG_DB_NAME: Optional[str] = os.getenv("RAG_DB_NAME", "legal_chunks_db_v2")

    # ----------------------------
    # OpenAI / LLM
    # ----------------------------
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: Optional[str] = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # ----------------------------
    # Google OAuth
    # ----------------------------
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: Optional[str] = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://127.0.0.1:8705/api/v1/auth/google/callback"
    )

    # ----------------------------
    # JWT Settings
    # ----------------------------
    JWT_SECRET_KEY: Optional[str] = os.getenv("JWT_SECRET_KEY", "supersecretkey123")
    JWT_ALGORITHM: Optional[str] = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

    # ----------------------------
    # Frontend URLs
    # ----------------------------
    FRONTEND_URL: Optional[str] = os.getenv("FRONTEND_URL", "http://localhost:8602")

    # ----------------------------
    # Default Knowledge Base
    # ----------------------------
    DEFAULT_KB: Optional[str] = os.getenv("DEFAULT_KB", "legal_chunks_db_v2")

    # ----------------------------
    # Firebase Authentication 🔥
    # ----------------------------
    FIREBASE_CREDENTIALS_PATH: Optional[str] = str(
        Path(
            os.getenv(
                "FIREBASE_CREDENTIALS_PATH",
                BASE_DIR / "service-account-key.json"
            )
        ).resolve()
    )

    # ----------------------------
    # Debug Mode for RAG Retrieval
    # ----------------------------
    DEBUG_RAG: bool = os.getenv("DEBUG_RAG", "False").lower() in ("true", "1", "yes")

    # ----------------------------
    # App Environment
    # ----------------------------
    APP_ENV: Optional[str] = APP_ENV


# ----------------------------------------------------
# Singleton accessor
# ----------------------------------------------------
@lru_cache()
def get_settings():
    s = Settings()

    print("============================================")
    print(f"✅ Environment Mode: {s.APP_ENV.upper()}")
    print(f"🔌 Backend DB: {s.POSTGRES_DB} @ {s.POSTGRES_HOST}:{s.POSTGRES_PORT}")
    if s.RAG_DB_NAME:
        print(f"🔌 RAG DB: {s.RAG_DB_NAME} @ {s.POSTGRES_HOST}:{s.POSTGRES_PORT}")
    else:
        print("⚠️ RAG_DB_NAME not configured in environment!")

    print("--------------------------------------------")
    print(f"✅ Loaded OpenAI Key? {bool(s.OPENAI_API_KEY)}")
    if s.OPENAI_API_KEY:
        print(f"   Key starts with: {s.OPENAI_API_KEY[:10]}")

    print(f"✅ Google Client ID Loaded? {bool(s.GOOGLE_CLIENT_ID)}")
    if s.GOOGLE_CLIENT_ID:
        print(f"   Client ID starts with: {s.GOOGLE_CLIENT_ID[:10]}...")

    print(f"✅ Redirect URI: {s.GOOGLE_REDIRECT_URI}")
    print(f"✅ FRONTEND_URL: {s.FRONTEND_URL}")
    print(f"✅ DEFAULT_KB: {s.DEFAULT_KB}")
    print(f"🔥 Firebase Credentials Path: {s.FIREBASE_CREDENTIALS_PATH}")
    print(f"🧩 DEBUG_RAG Mode: {s.DEBUG_RAG}")
    print("============================================")

    return s
