# Instalação (VPS)

## Requisitos

- Docker + Docker Compose
- Portas 3000 (web) e 8000 (API) livres — ou ajuste o compose
- GenieACS NBI alcançável **a partir da VPS** (firewall: só IP do Mr9)

## Passos

```bash
git clone https://github.com/mauroalx/Mr9.git
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
./scripts/bootstrap.sh # gera também a senha do PostgreSQL
docker compose up -d --build
```

Defina `MR9_CORS_ORIGINS` com a origem HTTPS pública. Coloque TLS na frente (Caddy/Nginx). Sample em `deploy/nginx.sample.conf`.

O compose de produção não publica o PostgreSQL e vincula web/API a `127.0.0.1`. Não remova essas restrições sem um firewall equivalente.

## Atualização

```bash
docker compose exec -T postgres pg_dump -U mr9 mr9 > mr9-backup.sql
git pull --ff-only
docker compose up -d --build
```

A imagem da API executa `alembic upgrade head` antes de iniciar.

### Bancos anteriores à versão 0.1.0

As versões locais anteriores não registravam revisão Alembic. Faça backup e, depois de confirmar que o sistema antigo iniciou pelo menos uma vez com o código mais recente, marque a base e aplique atualizações:

```bash
docker compose run --rm api alembic stamp 730cf63cba2a
docker compose run --rm api alembic upgrade head
```

## Reset de instalação

Só em lab: dropar o volume Postgres remove Super Admin e settings. Em produção, planeje backup cifrado do volume.
