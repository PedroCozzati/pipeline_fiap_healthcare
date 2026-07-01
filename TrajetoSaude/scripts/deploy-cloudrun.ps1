# Provisiona a infraestrutura GCP completa e implanta todos os microserviços no Cloud Run
# (sem depender de Docker local). Substitui o fluxo "docker compose up" pelo equivalente em nuvem.
#
# Pré-requisitos: gcloud autenticado, Terraform >= 1.5, Docker, billing ativo no projeto.
#
# Uso:
#   .\scripts\deploy-cloudrun.ps1
#   .\scripts\deploy-cloudrun.ps1 -ProjectId "meu-projeto-123"

param(
     [string]$ProjectId = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$InfraDir = Join-Path $Root "infra"
$TfVars = Join-Path $InfraDir "terraform.tfvars"
$TfVarsExample = Join-Path $InfraDir "terraform.tfvars.example"

function Require-Command($Name) {
     if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
          throw "Comando obrigatório não encontrado: $Name"
     }
}

function Confirm-Apply($PlanFile) {
     $confirm = Read-Host "`nAplicar o plano acima? (s/N)"
     if ($confirm -notin @("s", "S", "sim", "Sim", "y", "Y")) {
          Write-Host "Cancelado."
          exit 0
     }
     terraform apply $PlanFile
}

Require-Command terraform
Require-Command gcloud
Require-Command docker

if (-not (Test-Path $TfVars)) {
     if ($ProjectId -eq "") {
          $ProjectId = Read-Host "Informe o GCP project_id"
     }
     Copy-Item $TfVarsExample $TfVars
     (Get-Content $TfVars) -replace 'seu-projeto-gcp', $ProjectId | Set-Content $TfVars
     Write-Host "Criado $TfVars com project_id=$ProjectId"
}

Push-Location $InfraDir
try {
     Write-Host "`n==> [1/4] terraform init" -ForegroundColor Cyan
     terraform init

     Write-Host "`n==> [2/4] terraform plan — infraestrutura base (Cloud SQL, GCS, Artifact Registry, SA)" -ForegroundColor Cyan
     terraform plan -var="deploy_cloud_run=false" -out tfplan-base
     Confirm-Apply tfplan-base
}
finally {
     Pop-Location
}

Write-Host "`n==> [3/4] Build e push das imagens Docker para o Artifact Registry" -ForegroundColor Cyan
& (Join-Path $Root "scripts\build-push.ps1")

Push-Location $InfraDir
try {
     Write-Host "`n==> [4/4] terraform plan — serviços Cloud Run" -ForegroundColor Cyan
     terraform plan -var="deploy_cloud_run=true" -out tfplan-cloudrun
     Confirm-Apply tfplan-cloudrun

     Write-Host "`n=== URLs dos serviços ===" -ForegroundColor Green
     $GatewayUrl = terraform output -raw cloud_run_gateway_url
     Write-Host "Frontend:   $(terraform output -raw cloud_run_frontend_url)"
     Write-Host "Gateway:    $GatewayUrl"
     Write-Host "Auth:       $(terraform output -raw cloud_run_auth_url)"
     Write-Host "Storage:    $(terraform output -raw cloud_run_storage_url)"
     Write-Host "Prediction: $(terraform output -raw cloud_run_prediction_url)"
     Write-Host "Sentinel:   $(terraform output -raw cloud_run_sentinel_url)"
}
finally {
     Pop-Location
}

Write-Host "`n==> Populando banco com dados de demonstração (POST /api/seed)" -ForegroundColor Cyan
for ($i = 0; $i -lt 30; $i++) {
     try {
          Invoke-RestMethod -Uri "$GatewayUrl/health" -TimeoutSec 3 | Out-Null
          break
     }
     catch {
          Start-Sleep -Seconds 2
     }
}
try {
     $seedResult = Invoke-RestMethod -Method Post -Uri "$GatewayUrl/api/seed"
     $seedResult | ConvertTo-Json -Depth 6
}
catch {
     Write-Host "Aviso: falha ao chamar /api/seed ($_)" -ForegroundColor Yellow
}

Write-Host "`nDeploy concluído." -ForegroundColor Green
Write-Host "Próximo passo (treinar o modelo):" -ForegroundColor Yellow
Write-Host '  $env:PREDICTION_URL = (terraform -chdir=infra output -raw cloud_run_prediction_url)' -ForegroundColor Yellow
Write-Host '  .\scripts\train-model.ps1' -ForegroundColor Yellow
