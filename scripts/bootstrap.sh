#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

WEAK_KEYS=(
  "change-me-to-a-long-random-string"
  "dev-only-change-me-please-use-bootstrap"
)

is_weak_key() {
  local key="$1"
  local w
  for w in "${WEAK_KEYS[@]}"; do
    [[ "$key" == "$w" ]] && return 0
  done
  [[ ${#key} -lt 24 ]] && return 0
  return 1
}

gen_secret() {
  openssl rand -hex 32 2>/dev/null || python3 -c 'import secrets; print(secrets.token_hex(32))'
}

upsert_env() {
  local key="$1"
  local value="$2"
  local tmp
  if grep -qE "^${key}=" .env 2>/dev/null; then
    tmp="$(mktemp)"
    sed "s|^${key}=.*|${key}=${value}|" .env > "$tmp"
    mv "$tmp" .env
  else
    printf '%s=%s\n' "$key" "$value" >> .env
  fi
}

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker é obrigatório." >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  secret="$(gen_secret)"
  postgres_password="$(gen_secret)"
  cat > .env <<EOF
MR9_SECRET_KEY=${secret}
MR9_POSTGRES_PASSWORD=${postgres_password}
MR9_CORS_ORIGINS=http://localhost:3000
EOF
  echo "Criado .env com MR9_SECRET_KEY forte."
else
  # shellcheck disable=SC1091
  set -a
  # carrega só chave sem source completo (evita executar .env)
  current="$(grep -E '^MR9_SECRET_KEY=' .env | head -1 | cut -d= -f2- | tr -d '\r' || true)"
  set +a
  if [[ -z "$current" ]] || is_weak_key "$current"; then
    secret="$(gen_secret)"
    if grep -qE '^MR9_SECRET_KEY=' .env; then
      # reescreve a linha mantendo o restante
      tmp="$(mktemp)"
      sed "s|^MR9_SECRET_KEY=.*|MR9_SECRET_KEY=${secret}|" .env > "$tmp"
      mv "$tmp" .env
    else
      printf '\nMR9_SECRET_KEY=%s\n' "$secret" >> .env
    fi
    echo "MR9_SECRET_KEY fraca/ausente substituída por chave forte."
    echo "IMPORTANTE: regrave os bearers NBI em Settings → Servidores ACS após o restart."
  else
    echo ".env ok (MR9_SECRET_KEY presente)."
  fi
  postgres_password="$(grep -E '^MR9_POSTGRES_PASSWORD=' .env | head -1 | cut -d= -f2- | tr -d '\r' || true)"
  if [[ ${#postgres_password} -lt 24 ]]; then
    upsert_env MR9_POSTGRES_PASSWORD "$(gen_secret)"
    echo "MR9_POSTGRES_PASSWORD ausente/fraca substituída por senha forte."
  fi
fi

echo
echo "Configuração preparada."
echo "Produção: docker compose up -d --build"
echo "Desenvolvimento: docker compose -f docker-compose.dev.yml up -d --build"
