#!/usr/bin/env bash
# Provisiona infraestrutura GCP com Terraform e gera .env + credenciais.
# Uso: ./scripts/setup-gcp.sh [project_id]

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA_DIR="$ROOT/infra"
TFVARS="$INFRA_DIR/terraform.tfvars"
TFVARS_EXAMPLE="$INFRA_DIR/terraform.tfvars.example"
CREDS_DIR="$ROOT/credentials"

command -v terraform >/dev/null || { echo "Terraform não encontrado."; exit 1; }
command -v gcloud >/dev/null || { echo "gcloud CLI não encontrado."; exit 1; }

PROJECT_ID="${1:-}"

if [[ ! -f "$TFVARS" ]]; then
     if [[ -z "$PROJECT_ID" ]]; then
          read -r -p "Informe o GCP project_id: " PROJECT_ID
     fi
     cp "$TFVARS_EXAMPLE" "$TFVARS"
     sed -i.bak "s/seu-projeto-gcp/$PROJECT_ID/" "$TFVARS" && rm -f "$TFVARS.bak"
     echo "Criado $TFVARS com project_id=$PROJECT_ID"
fi

mkdir -p "$CREDS_DIR"

cd "$INFRA_DIR"
terraform init
terraform plan -out tfplan
read -r -p "Aplicar o plano acima? (s/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[sSyY] ]]; then
     echo "Cancelado."
     exit 0
fi
terraform apply tfplan

"$ROOT/scripts/generate-env.sh"

echo ""
echo "Provisionamento concluído."
echo "Próximo passo: docker compose up --build"
