# Provisiona infraestrutura GCP com Terraform e gera .env + credenciais.
# Pré-requisitos: gcloud autenticado, Terraform >= 1.5, billing ativo no projeto.
#
# Uso:
#   .\scripts\setup-gcp.ps1
#   .\scripts\setup-gcp.ps1 -ProjectId "meu-projeto-123"

param(
     [string]$ProjectId = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$InfraDir = Join-Path $Root "infra"
$TfVars = Join-Path $InfraDir "terraform.tfvars"
$TfVarsExample = Join-Path $InfraDir "terraform.tfvars.example"
$CredsDir = Join-Path $Root "credentials"

function Require-Command($Name) {
     if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
          throw "Comando obrigatório não encontrado: $Name"
     }
}

Require-Command terraform
Require-Command gcloud

if (-not (Test-Path $TfVars)) {
     if ($ProjectId -eq "") {
          $ProjectId = Read-Host "Informe o GCP project_id"
     }
     Copy-Item $TfVarsExample $TfVars
     (Get-Content $TfVars) -replace 'seu-projeto-gcp', $ProjectId | Set-Content $TfVars
     Write-Host "Criado $TfVars com project_id=$ProjectId"
}

if (-not (Test-Path $CredsDir)) {
     New-Item -ItemType Directory -Path $CredsDir | Out-Null
}

Push-Location $InfraDir
try {
     Write-Host "`n==> terraform init" -ForegroundColor Cyan
     terraform init

     Write-Host "`n==> terraform plan" -ForegroundColor Cyan
     terraform plan -out tfplan

     $confirm = Read-Host "`nAplicar o plano acima? (s/N)"
     if ($confirm -notin @("s", "S", "sim", "Sim", "y", "Y")) {
          Write-Host "Cancelado."
          exit 0
     }

     Write-Host "`n==> terraform apply" -ForegroundColor Cyan
     terraform apply tfplan
}
finally {
     Pop-Location
}

& (Join-Path $Root "scripts\generate-env.ps1")

Write-Host "`nProvisionamento concluído." -ForegroundColor Green
Write-Host "Próximo passo: docker compose up --build" -ForegroundColor Yellow
