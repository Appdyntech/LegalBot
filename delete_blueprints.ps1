# ==============================
# Delete Render Blueprints via API
# ==============================

# 🔐 Your Render API key
$apiKey = "rnd_O21wFNmCDyCM4rblNLGvs55Bhgbr"

# 🧾 List of Blueprint IDs to delete
$blueprintIds = @(
    "exs-d3quv7ur433s73e1skr0"
)

# 🧠 Set headers for the API request
$headers = @{
    "Authorization" = "Bearer $apiKey"
    "Accept"        = "application/json"
}

# 🚀 Loop through and delete each Blueprint
foreach ($id in $blueprintIds) {
    Write-Host "`n🧹 Deleting Blueprint ID: $id ..." -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Uri "https://api.render.com/v1/blueprints/$id" `
            -Headers $headers `
            -Method Delete
        Write-Host "✅ Deleted: $id" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Failed to delete: $id" -ForegroundColor Red
        Write-Host $_.Exception.Message
    }
}
