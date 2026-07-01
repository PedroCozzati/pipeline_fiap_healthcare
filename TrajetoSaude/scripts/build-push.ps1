# Builda e envia as imagens Docker dos microserviços para o Artifact Registry.
# Pré-requisito: infra base já provisionada (terraform apply com deploy_cloud_run=false).
#
# Uso:
#   .\scripts\build-push.ps1
#   .\scripts\build-push.ps1 -ImageTag "v1"

param(
     [string]$ImageTag = "latest"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$InfraDir = Join-Path $Root "infra"

function Require-Command($Name) {
     if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
          throw "Comando obrigatório não encontrado: $Name"
     }
}

Require-Command terraform
Require-Command docker
Require-Command gcloud

Push-Location $InfraDir
try {
     $Registry = terraform output -raw artifact_registry_repository
     $Region = terraform output -raw region
}
finally {
     Pop-Location
}

if (-not $Registry) {
     throw "Não foi possível obter 'artifact_registry_repository'. Execute 'terraform apply' antes."
}

Write-Host "`n==> Autenticando Docker no Artifact Registry ($Region)" -ForegroundColor Cyan
gcloud auth configure-docker "$Region-docker.pkg.dev" --quiet

# Nome do serviço | diretório de contexto (relativo a TrajetoSaude) | Dockerfile (relativo ao contexto)
$Services = @(
     @{ Name = "auth";       Context = "auth";       Dockerfile = "Dockerfile" },
     @{ Name = "storage";    Context = "storage";    Dockerfile = "Dockerfile" },
     @{ Name = "sentinel";   Context = "sentinel_ai"; Dockerfile = "Dockerfile" },
     @{ Name = "gateway";    Context = "gateway";    Dockerfile = "Dockerfile" },
     @{ Name = "prediction"; Context = ".";           Dockerfile = "prediction/Dockerfile.cloudrun" },
     @{ Name = "frontend";   Context = "frontend";    Dockerfile = "Dockerfile.cloudrun" }
)

Push-Location $Root
try {
     foreach ($svc in $Services) {
          $image = "$Registry/$($svc.Name):$ImageTag"
          $dockerfilePath = Join-Path $svc.Context $svc.Dockerfile

          Write-Host "`n==> Build: $($svc.Name)" -ForegroundColor Cyan
          docker build -t $image -f $dockerfilePath $svc.Context
          if ($LASTEXITCODE -ne 0) { throw "Build falhou para $($svc.Name)" }

          Write-Host "==> Push: $image" -ForegroundColor Cyan
          docker push $image
          if ($LASTEXITCODE -ne 0) { throw "Push falhou para $($svc.Name)" }
     }
}
finally {
     Pop-Location
}

Write-Host "`nTodas as imagens enviadas para $Registry (tag: $ImageTag)" -ForegroundColor Green
