#!/usr/bin/env bash
# Gera TrajetoSaude/.env a partir dos outputs do Terraform.
# Uso: ./scripts/generate-env.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA_DIR="$ROOT/infra"
ENV_FILE="$ROOT/.env"

cd "$INFRA_DIR"
CONTENT="$(terraform output -raw env_file_content)"

if [[ -z "$CONTENT" ]]; then
     echo "Output 'env_file_content' vazio. Execute 'terraform apply' antes." >&2
     exit 1
fi

printf '%s\n' "$CONTENT" > "$ENV_FILE"
echo "Arquivo gerado: $ENV_FILE"
