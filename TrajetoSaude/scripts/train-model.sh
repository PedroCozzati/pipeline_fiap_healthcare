#!/usr/bin/env bash
# Treina o modelo de risco via API do microserviço prediction.
# Uso: ./scripts/train-model.sh

set -euo pipefail

BASE_URL="${PREDICTION_URL:-http://localhost:8002}"

echo "Aguardando prediction em $BASE_URL ..."
for _ in $(seq 1 30); do
     if curl -sf "$BASE_URL/health" >/dev/null; then
          break
     fi
     sleep 2
done

echo "Executando pipeline de ingestão/treino..."
curl -sf -X POST "$BASE_URL/ingest/run" | python -m json.tool
echo "Modelo treinado. Verifique prediction/artefatos/risk_model.joblib"
