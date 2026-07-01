#!/usr/bin/env bash
# Builda e envia as imagens Docker dos microserviços para o Artifact Registry.
# Pré-requisito: infra base já provisionada (terraform apply com deploy_cloud_run=false).
#
# Uso:
#   ./scripts/build-push.sh
#   ./scripts/build-push.sh v1   # tag customizada

set -euo pipefail

IMAGE_TAG="${1:-latest}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA_DIR="$ROOT/infra"

command -v terraform >/dev/null || { echo "terraform não encontrado" >&2; exit 1; }
command -v docker >/dev/null || { echo "docker não encontrado" >&2; exit 1; }
command -v gcloud >/dev/null || { echo "gcloud não encontrado" >&2; exit 1; }

pushd "$INFRA_DIR" >/dev/null
REGISTRY="$(terraform output -raw artifact_registry_repository)"
REGION="$(terraform output -raw region)"
popd >/dev/null

if [ -z "$REGISTRY" ]; then
  echo "Não foi possível obter 'artifact_registry_repository'. Execute 'terraform apply' antes." >&2
  exit 1
fi

echo
echo "==> Autenticando Docker no Artifact Registry ($REGION)"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

declare -A CONTEXTS=(
  [auth]="auth"
  [storage]="storage"
  [sentinel]="sentinel_ai"
  [gateway]="gateway"
  [prediction]="."
  [frontend]="frontend"
)

declare -A DOCKERFILES=(
  [auth]="Dockerfile"
  [storage]="Dockerfile"
  [sentinel]="Dockerfile"
  [gateway]="Dockerfile"
  [prediction]="prediction/Dockerfile.cloudrun"
  [frontend]="Dockerfile.cloudrun"
)

cd "$ROOT"

for service in auth storage sentinel gateway prediction frontend; do
  context="${CONTEXTS[$service]}"
  dockerfile="${DOCKERFILES[$service]}"
  image="${REGISTRY}/${service}:${IMAGE_TAG}"

  echo
  echo "==> Build: ${service}"
  docker build -t "$image" -f "${context}/${dockerfile}" "$context"

  echo "==> Push: $image"
  docker push "$image"
done

echo
echo "Todas as imagens enviadas para ${REGISTRY} (tag: ${IMAGE_TAG})"
