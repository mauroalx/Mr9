#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker é obrigatório." >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  secret="$(openssl rand -hex 32 2>/dev/null || python3 -c 'import secrets; print(secrets.token_hex(32))')"
  cat > .env <<EOF
MR9_SECRET_KEY=${secret}
MR9_DATABASE_URL=postgresql+psycopg://mr9:mr9@postgres:5432/mr9
MR9_CORS_ORIGINS=http://localhost:3000
EOF
  echo "Criado .env com MR9_SECRET_KEY."
fi

echo "Subindo stack (dev)…"
docker compose -f docker-compose.dev.yml up -d --build postgres
docker compose -f docker-compose.dev.yml up -d --build api
echo
echo "API:  http://localhost:8000/api/v1/health"
echo "Web:  cd apps/web && npm run dev   (ou docker compose -f docker-compose.dev.yml up web)"
echo "Wizard: http://localhost:3000/setup"
echo
echo "Pronto. Conclua o wizard e libere o GenieACS NBI só para o IP desta VPS."
