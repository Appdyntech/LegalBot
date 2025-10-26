"""
auth_google.py
Handles Google OAuth2 Login, Callback (redirects to frontend), and Token Verification for LegalBOT.
"""

import os
import time
import jwt
import httpx
import logging
from urllib.parse import urlencode
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from pydantic import BaseModel
from uuid import uuid4

# ✅ Updated imports for new structure
from app.config import get_settings
from app.db_postgres import get_postgres_conn

# -----------------------------------------------------
# INIT
# -----------------------------------------------------
settings = get_settings()
router = APIRouter(prefix="/google", tags=["Google Auth"])

logger = logging.getLogger("auth_google")
logger.setLevel(logging.INFO)

# -----------------------------------------------------
# CONFIG
# -----------------------------------------------------
GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = getattr(settings, "GOOGLE_CLIENT_SECRET", None)
GOOGLE_REDIRECT_URI = getattr(
    settings, "GOOGLE_REDIRECT_URI", "http://127.0.0.1:8705/api/v1/auth/google/callback"
)
FRONTEND_REDIRECT_URI = f"{settings.FRONTEND_URL}/google/callback"

JWT_SECRET = getattr(settings, "JWT_SECRET_KEY", "supersecretjwt")
JWT_ALGO = getattr(settings, "JWT_ALGORITHM", "HS256")
JWT_EXPIRATION = getattr(settings, "JWT_EXPIRATION_MINUTES", 60)


class TokenRequest(BaseModel):
    token: str


# -----------------------------------------------------
# HELPERS
# -----------------------------------------------------
def create_jwt_token(email: str, name: str, picture: str = None):
    """Generate a short-lived JWT for LegalBOT session management."""
    payload = {
        "sub": email,
        "name": name,
        "picture": picture,
        "iat": int(time.time()),
        "exp": int(time.time()) + (JWT_EXPIRATION * 60),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    return token


# -----------------------------------------------------
# ROUTES
# -----------------------------------------------------
@router.get("/login")
async def google_login():
    """Redirect user to Google OAuth2 consent page."""
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    logger.info(f"🔗 Redirecting user to: {url}")
    return RedirectResponse(url=url)


@router.get("/callback")
async def google_callback(request: Request):
    """Handle Google OAuth callback and redirect to frontend."""
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    logger.info(f"📩 Received OAuth code: {code[:10]}...")

    try:
        # --- Exchange code for tokens ---
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            }
            response = await client.post(token_url, data=data)
            token_data = response.json()

        if "id_token" not in token_data:
            raise HTTPException(status_code=400, detail=f"Invalid Google response: {token_data}")

        # --- Verify ID token ---
        idinfo = id_token.verify_oauth2_token(
            token_data["id_token"], google_requests.Request(), GOOGLE_CLIENT_ID
        )

        email = idinfo.get("email")
        name = idinfo.get("name")
        picture = idinfo.get("picture")

        jwt_token = create_jwt_token(email=email, name=name, picture=picture)

        # --- Sync user in Postgres ---
        try:
            conn = get_postgres_conn()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO customers (customer_id, name, email, google_verified, auth_provider, active)
                VALUES (%s, %s, %s, TRUE, 'google', TRUE)
                ON CONFLICT (email) DO UPDATE
                SET name = EXCLUDED.name,
                    google_verified = TRUE,
                    auth_provider = 'google',
                    active = TRUE;
                """,
                (str(uuid4()), name, email),
            )
            conn.commit()
            logger.info(f"✅ Google user synced: {email}")

        except Exception as db_err:
            logger.error(f"❌ DB sync failed for Google user {email}: {db_err}")
            if conn:
                conn.rollback()
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

        # --- Redirect to frontend ---
        params = urlencode({
            "jwt": jwt_token,
            "email": email,
            "name": name,
            "picture": picture or "",
        })
        redirect_url = f"{FRONTEND_REDIRECT_URI}?{params}"
        logger.info(f"🔁 Redirecting to frontend: {redirect_url}")

        return RedirectResponse(url=redirect_url)

    except Exception as e:
        logger.error(f"❌ [google_callback] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Google auth failed: {str(e)}")


@router.post("/verify")
async def verify_google_token(data: TokenRequest):
    """Verify Google ID token directly (used by SPA/mobile apps)."""
    try:
        idinfo = id_token.verify_oauth2_token(
            data.token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
        email = idinfo.get("email")
        name = idinfo.get("name")
        picture = idinfo.get("picture")

        jwt_token = create_jwt_token(email=email, name=name, picture=picture)
        logger.info(f"✅ Verified Google token for {email}")
        return {
            "status": "verified",
            "email": email,
            "name": name,
            "picture": picture,
            "jwt": jwt_token,
        }

    except Exception as e:
        logger.error(f"❌ [verify_google_token] Error: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
