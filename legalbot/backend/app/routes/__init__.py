# backend/app/routes/__init__.py
# Empty init to mark this as a package
# backend/app/routes/__init__.py
from . import (
    chat,
    classify,
    customer,
    documents,
    lawyers,
    notifications,
    payments,
    health,
)

__all__ = [
    "chat",
    "classify",
    "customer",
    "documents",
    "lawyers",
    "notifications",
    "payments",
    "health",
]
