#!/usr/bin/env bash
# Reempacota o código-fonte dos agentes ADK (agent.py + requirements.txt) em
# infra/agents/<nome>/source.tar.gz.b64, consumido pelo Terraform via
# source_code_spec.inline_source no google_vertex_ai_reasoning_engine.
#
# Rode este script sempre que editar infra/agents/<nome>/agent.py, e então
# rode terraform apply para publicar a nova versão do agente.
#
# Uso:
#   ./infra/scripts/package-agents.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENTS_DIR="$ROOT/agents"

for dir in "$AGENTS_DIR"/*/; do
  name="$(basename "$dir")"
  [ -f "$dir/agent.py" ] || continue

  echo "==> Empacotando $name"
  tar -czf "$dir/source.tar.gz" -C "$dir" agent.py requirements.txt
  base64 -w 0 "$dir/source.tar.gz" > "$dir/source.tar.gz.b64"
  rm -f "$dir/source.tar.gz"
done

echo "Pronto. Rode 'terraform apply' em infra/ para publicar as mudanças."
