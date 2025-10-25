# legalbot/backend/app/middleware/cors_middleware.py

from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app):
    origins = [
        "http://localhost:8602",
        "http://localhost:8705",
        "https://legalbot-frontend-fajw.onrender.com",
        "https://legalbot-backend-ew4x.onrender.com",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
