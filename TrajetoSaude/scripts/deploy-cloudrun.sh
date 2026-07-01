#!/usr/bin/env bash
# Provisiona a infraestrutura GCP completa e implanta todos os microserviços no Cloud Run
# (sem depender de Docker local). Substitui o fluxo "docker compose up" pelo equivalente em nuvem.
#
# Pré-requisitos: gcloud autenticado, Terraform >= 1.5, Docker, billing ativo no projeto.
#
# Uso:
#   ./scripts/deploy-cloudrun.sh [project_id]

set -euo pipefail

PROJECT_ID="${1:-}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA_DIR="$ROOT/infra"
TF_VARS="$INFRA_DIR/terraform.tfvars"
TF_VARS_EXAMPLE="$INFRA_DIR/terraform.tfvars.example"

command -v terraform >/dev/null || { echo "terraform não encontrado" >&2; exit 1; }
command -v gcloud >/dev/null || { echo "gcloud não encontrado" >&2; exit 1; }
command -v docker >/dev/null || { echo "docker não encontrado" >&2; exit 1; }

confirm_apply() {
  read -r -p $'\nAplicar o plano acima? (s/N) ' reply
  case "$reply" in
    s|S|sim|Sim|y|Y) terraform apply "$1" ;;
    *) echo "Cancelado."; exit 0 ;;
  esac
}

if [ ! -f "$TF_VARS" ]; then
  if [ -z "$PROJECT_ID" ]; then
    read -r -p "Informe o GCP project_id: " PROJECT_ID
  fi
  cp "$TF_VARS_EXAMPLE" "$TF_VARS"
  sed -i.bak "s/seu-projeto-gcp/${PROJECT_ID}/" "$TF_VARS" && rm -f "$TF_VARS.bak"
  echo "Criado $TF_VARS com project_id=${PROJECT_ID}"
fi

pushd "$INFRA_DIR" >/dev/null

echo
echo "==> [1/4] terraform init"
terraform init

echo
echo "==> [2/4] terraform plan — infraestrutura base (Cloud SQL, GCS, Artifact Registry, SA)"
terraform plan -var="deploy_cloud_run=false" -out tfplan-base
confirm_apply tfplan-base

popd >/dev/null

echo
echo "==> [3/4] Build e push das imagens Docker para o Artifact Registry"
"$ROOT/scripts/build-push.sh"

pushd "$INFRA_DIR" >/dev/null

echo
echo "==> [4/4] terraform plan — serviços Cloud Run"
terraform plan -var="deploy_cloud_run=true" -out tfplan-cloudrun
confirm_apply tfplan-cloudrun

echo
echo "=== URLs dos serviços ==="
GATEWAY_URL="$(terraform output -raw cloud_run_gateway_url)"
echo "Frontend:   $(terraform output -raw cloud_run_frontend_url)"
echo "Gateway:    $GATEWAY_URL"
echo "Auth:       $(terraform output -raw cloud_run_auth_url)"
echo "Storage:    $(terraform output -raw cloud_run_storage_url)"
echo "Prediction: $(terraform output -raw cloud_run_prediction_url)"
echo "Sentinel:   $(terraform output -raw cloud_run_sentinel_url)"

popd >/dev/null

echo
echo "==> Populando banco com dados de demonstração (POST /api/seed)"
for i in $(seq 1 30); do
  curl -sf "$GATEWAY_URL/health" >/dev/null 2>&1 && break
  sleep 2
done
curl -sf -X POST "$GATEWAY_URL/api/seed" -H 'accept: application/json' -d '' \
  || echo "Aviso: falha ao chamar /api/seed"

echo
echo "Deploy concluído."
echo "Próximo passo (treinar o modelo):"
echo "  PREDICTION_URL=\$(terraform -chdir=infra output -raw cloud_run_prediction_url) ./scripts/train-model.sh"
