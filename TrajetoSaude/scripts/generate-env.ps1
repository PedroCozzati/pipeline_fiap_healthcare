# Gera TrajetoSaude/.env a partir dos outputs do Terraform.
# Uso: .\scripts\generate-env.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$InfraDir = Join-Path $Root "infra"
$EnvFile = Join-Path $Root ".env"

Push-Location $InfraDir
try {
     $content = terraform output -raw env_file_content
     if (-not $content) {
          throw "Output 'env_file_content' vazio. Execute 'terraform apply' antes."
     }
     Set-Content -Path $EnvFile -Value $content -Encoding UTF8
     Write-Host "Arquivo gerado: $EnvFile" -ForegroundColor Green
}
finally {
     Pop-Location
}
