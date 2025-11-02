# backend/app/auth_firebase.py
import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import get_settings
import os

settings = get_settings()
security = HTTPBearer()

# ✅ Initialize Firebase only once (singleton)
if not firebase_admin._apps:
    try:
        cred_path = settings.FIREBASE_CREDENTIALS_PATH
        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"Firebase credentials file not found: {cred_path}")

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print(f"[auth_firebase] ✅ Firebase initialized from: {cred_path}")
    except Exception as e:
        print(f"[auth_firebase] ❌ Failed to initialize Firebase: {e}")
        raise

# ✅ Verify ID Token Dependency
def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    try:
        decoded = auth.verify_id_token(token)
        print(f"[auth_firebase] ✅ Verified Firebase user: {decoded.get('email')}")
        return decoded
    except Exception as e:
        print(f"[auth_firebase] ❌ Invalid Firebase token: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired Firebase token")
