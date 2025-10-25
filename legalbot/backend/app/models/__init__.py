# backend/app/models/__init__.py
from sqlalchemy.ext.declarative import declarative_base

# ✅ Define global declarative base for all models
Base = declarative_base()

# Optional: import specific model files here if you have them
# from .chat_history import ChatHistory
