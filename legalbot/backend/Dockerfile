# ==========================
# Backend Dockerfile
# ==========================
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and netcat (for DB wait script)
RUN apt-get update && apt-get install -y \
    build-essential \
    netcat-openbsd \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Ensure Google and JWT dependencies are installed
RUN pip install google-auth google-auth-oauthlib google-auth-httplib2 PyJWT

# Copy backend source code
COPY backend/app /app/app

# Copy wait-for-db script and make it executable
COPY backend/app/wait-for-db.sh /app/wait-for-db.sh
RUN chmod +x /app/wait-for-db.sh

# Expose the backend port
EXPOSE 8705

# Run backend (waits for DB first)
CMD ["bash", "/app/wait-for-db.sh", "db", "5432", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8705"]

