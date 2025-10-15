import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional
from functools import lru_cache

# ----------------------------------------------------
# Load environment
# ----------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / ".env"
loaded = load_dotenv(dotenv_path=ENV_PATH, override=True)
print(f"🔍 Loading .env from {ENV_PATH} (success={loaded})")


class Settings:
    # ----------------------------
    # MongoDB
    # ----------------------------
    MONGO_URI: Optional[str] = os.getenv("MONGO_URI", "")
    MONGO_DB: Optional[str] = os.getenv("MONGO_DB", "digitized_docs_db")
    MONGO_COLLECTION: Optional[str] = os.getenv("MONGO_COLLECTION", "digitized_docs")

    # ----------------------------
    # PostgreSQL
    # ----------------------------
    POSTGRES_HOST: Optional[str] = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: Optional[str] = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: Optional[str] = os.getenv("POSTGRES_DB", "legalbot")
    POSTGRES_USER: Optional[str] = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: Optional[str] = os.getenv("POSTGRES_PASSWORD", "")

    # ----------------------------
    # OpenAI / LLM
    # ----------------------------
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: Optional[str] = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # ----------------------------
    # Local LLM (optional)
    # ----------------------------
    LOCAL_LLM_PATH: Optional[str] = os.getenv("LOCAL_LLM_PATH", "")

    # ----------------------------
    # Twilio / WhatsApp
    # ----------------------------
    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_NUMBER: Optional[str] = os.getenv("TWILIO_WHATSAPP_NUMBER", "")

    # ----------------------------
    # Google OAuth
    # ----------------------------
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: Optional[str] = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://127.0.0.1:8705/api/v1/auth/google/callback"
    )

    # ----------------------------
    # JWT Settings (used for internal auth)
    # ----------------------------
    JWT_SECRET_KEY: Optional[str] = os.getenv("JWT_SECRET_KEY", "supersecretkey123")
    JWT_ALGORITHM: Optional[str] = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

    # ----------------------------
    # App Defaults
    # ----------------------------
    DEFAULT_KB: Optional[str] = os.getenv("DEFAULT_KB", "digitized_docs")
    CHAT_CSV_PATH: Optional[str] = os.getenv("CHAT_CSV_PATH", "chat_history.csv")

    # ----------------------------
    # ✅ NEW FRONTEND CONFIG
    # ----------------------------
    FRONTEND_URL: Optional[str] = os.getenv("FRONTEND_URL", "http://localhost:8602")


# ----------------------------------------------------
# Singleton accessor
# ----------------------------------------------------
@lru_cache()
def get_settings():
    s = Settings()
    print(f"✅ Loaded OpenAI Key? {bool(s.OPENAI_API_KEY)}")
    if s.OPENAI_API_KEY:
        print(f"✅ OpenAI Key starts with: {s.OPENAI_API_KEY[:10]}")
    print(f"✅ Loaded Google Client ID? {bool(s.GOOGLE_CLIENT_ID)}")
    if s.GOOGLE_CLIENT_ID:
        print(f"✅ Google Client ID starts with: {s.GOOGLE_CLIENT_ID[:10]}...")
    print(f"✅ Google Redirect URI: {s.GOOGLE_REDIRECT_URI}")
    print(f"✅ FRONTEND_URL: {s.FRONTEND_URL}")
    return s
