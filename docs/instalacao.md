# Instalação (VPS)

## Requisitos

- Docker + Docker Compose
- Portas 3000 (web) e 8000 (API) livres — ou ajuste o compose
- GenieACS NBI alcançável **a partir da VPS** (firewall: só IP do Mr9)

## Passos

```bash
git clone <seu-fork-mr9>.git
cd Mr9
./scripts/bootstrap.sh
```

Suba a web (dev) ou use o serviço `web` do compose:

```bash
docker compose -f docker-compose.dev.yml up --build
```

1. Abra `http://SEU_IP:3000/setup`
2. Crie o **Super Admin**
3. Configure DNS aprovados / limiar online
4. Cadastre o GenieACS (URL + Bearer) — o wizard testa o NBI no backend
5. Conclua e faça login

## Produção

```bash
cp .env.example .env   # defina MR9_SECRET_KEY forte
docker compose up -d --build
```

Coloque TLS na frente (Caddy/Nginx). Sample em `deploy/nginx.sample.conf`.

## Reset de instalação

Só em lab: dropar o volume Postgres remove Super Admin e settings. Em produção, planeje backup cifrado do volume.
