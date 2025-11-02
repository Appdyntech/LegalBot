import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..config import get_settings

settings = get_settings()
security = HTTPBearer()

# Initialize Firebase Admin SDK once
if not firebase_admin._apps:
    cred_path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", None)
    if not cred_path:
        raise RuntimeError("FIREBASE_CREDENTIALS_PATH missing in environment.")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)


def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verifies Firebase ID Token from Authorization header."""
    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        return {
            "uid": decoded_token.get("uid"),
            "email": decoded_token.get("email"),
            "name": decoded_token.get("name"),
            "picture": decoded_token.get("picture"),
        }
    except Exception as e:
        print(f"[auth_firebase] ❌ Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid Firebase ID token")
