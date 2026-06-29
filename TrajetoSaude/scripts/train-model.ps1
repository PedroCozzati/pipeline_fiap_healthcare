# Treina o modelo de risco via API do microserviço prediction (dados demo ou risk_training.csv).
# Uso: .\scripts\train-model.ps1

$ErrorActionPreference = "Stop"
$BaseUrl = if ($env:PREDICTION_URL) { $env:PREDICTION_URL } else { "http://localhost:8002" }

Write-Host "Aguardando prediction em $BaseUrl ..."
for ($i = 0; $i -lt 30; $i++) {
     try {
          Invoke-RestMethod -Uri "$BaseUrl/health" -TimeoutSec 3 | Out-Null
          break
     }
     catch {
          Start-Sleep -Seconds 2
     }
}

Write-Host "Executando pipeline de ingestão/treino..."
$result = Invoke-RestMethod -Method Post -Uri "$BaseUrl/ingest/run"
$result | ConvertTo-Json -Depth 6
Write-Host "Modelo treinado. Verifique prediction/artefatos/risk_model.joblib" -ForegroundColor Green
