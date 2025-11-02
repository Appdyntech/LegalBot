# backend/app/auth.py
import os
import jwt
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
from urllib.parse import urlencode

from ..config import get_settings

router = APIRouter(tags=["Auth"])
settings = get_settings()

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------
GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI = settings.GOOGLE_REDIRECT_URI
FRONTEND_URL = settings.FRONTEND_URL
JWT_SECRET = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM


# ----------------------------------------------------
# STEP 1 — LOGIN (redirect to Google)
# ----------------------------------------------------
@router.get("/auth/google/login")
async def google_login():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url)


# ----------------------------------------------------
# STEP 2 — CALLBACK (Google → backend)
# ----------------------------------------------------
@router.get("/auth/google/callback")
async def google_callback(code: str):
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    token_response = requests.post(token_url, data=data)
    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Google token error: {token_response.text}")

    tokens = token_response.json()
    id_token = tokens.get("id_token")
    userinfo = jwt.decode(id_token, options={"verify_signature": False})

    email = userinfo.get("email")
    name = userinfo.get("name")
    picture = userinfo.get("picture")

    if not email:
        raise HTTPException(status_code=400, detail="Invalid Google response: missing email")

    payload = {
        "sub": email,
        "name": name,
        "picture": picture,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
    }

    jwt_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    print(f"[auth_google] ✅ Authenticated user: {email}")

    redirect_url = (
        f"{FRONTEND_URL}/google/callback?"
        f"jwt={jwt_token}&email={email}&name={name}&picture={picture}"
    )

    return RedirectResponse(redirect_url)
