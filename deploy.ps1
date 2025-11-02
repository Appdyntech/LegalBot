# ============================================
# 🚀 LegalBOT Cloud Deployment Script (GCP)
# Author: Joy + ChatGPT
# ============================================

# Stop on first error
$ErrorActionPreference = "Stop"

Write-Host "`n============================================"
Write-Host "🚀 Starting LegalBOT Backend Deployment"
Write-Host "============================================`n"

# ----------------------------
# 1️⃣ Verify gcloud CLI
# ----------------------------
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Google Cloud SDK not found in PATH. Exiting." -ForegroundColor Red
    exit 1
}

# ----------------------------
# 2️⃣ Define constants
# ----------------------------
$PROJECT_ID = "legalcbot"
$REGION = "us-central1"
$SERVICE_NAME = "legalbot-backend"
$IMAGE = "gcr.io/$PROJECT_ID/$SERVICE_NAME"
$CLOUDSQL_INSTANCE = "legalcbot:us-central1:legalbot-db"
$DOCKERFILE = "Dockerfile.backend"

# ----------------------------
# 3️⃣ Confirm Dockerfile exists
# ----------------------------
if (-not (Test-Path $DOCKERFILE)) {
    Write-Host "⚠️ Dockerfile.backend not found. Trying 'Dockerfile' instead..."
    if (-not (Test-Path "Dockerfile")) {
        Write-Host "❌ No Dockerfile found in current directory. Please check." -ForegroundColor Red
        exit 1
    } else {
        $DOCKERFILE = "Dockerfile"
    }
}

# ----------------------------
# 4️⃣ Build container image
# ----------------------------
Write-Host "🏗️ Building container image..."
gcloud builds submit --tag $IMAGE --file $DOCKERFILE .

# ----------------------------
# 5️⃣ Deploy to Cloud Run
# ----------------------------
Write-Host "`n🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME `
  --image $IMAGE `
  --region $REGION `
  --platform managed `
  --allow-unauthenticated `
  --add-cloudsql-instances $CLOUDSQL_INSTANCE `
  --set-env-vars APP_ENV=prod `
  --set-env-vars POSTGRES_HOST=/cloudsql/$CLOUDSQL_INSTANCE,POSTGRES_PORT=5432,POSTGRES_DB=legalbot,POSTGRES_USER=postgres,POSTGRES_PASSWORD=Google@123 `
  --set-env-vars RAG_DB_NAME=legal_chunks_db_v2,RAG_DB_USER=postgres,RAG_DB_PASSWORD=Google@123,RAG_DB_HOST=/cloudsql/$CLOUDSQL_INSTANCE,RAG_DB_PORT=5432 `
  --set-env-vars FRONTEND_URL=https://legalbot-frontend.web.app,OPENAI_MODEL=gpt-4o-mini

# ----------------------------
# 6️⃣ Get service URL
# ----------------------------
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format "value(status.url)"
Write-Host "`n✅ Deployment complete!"
Write-Host "🌐 Service URL: $SERVICE_URL"

# ----------------------------
# 7️⃣ Health check
# ----------------------------
Write-Host "`n🔍 Running health check..."
try {
    $health = Invoke-RestMethod -Uri "$SERVICE_URL/api/v1/health"
    Write-Host "`n✅ Health Check Result:" -ForegroundColor Green
    $health | ConvertTo-Json -Depth 5
} catch {
    Write-Host "⚠️ Health check failed — please verify manually." -ForegroundColor Yellow
}
