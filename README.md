# Mr9

**Mr9** é um micro-ACS open source para operar **GenieACS** (NBI HTTP + Bearer), com UI própria, wizard de instalação em VPS, multi-ACS, ACL por grupos, diagnóstico e dashboard.

> O browser **nunca** fala com o GenieACS — só a API Mr9. Facilita firewall e evita CORS.

## Stack

- **Web:** Next.js + Tailwind (identidade “Fiber control room”)
- **API:** FastAPI + SQLAlchemy + Postgres
- **Docker:** `docker-compose.yml` (prod-like) e `docker-compose.dev.yml`

## Subir rápido

```bash
./scripts/bootstrap.sh
cd apps/web && npm install && npm run dev
# API: docker compose -f docker-compose.dev.yml up api
```

Abra `http://localhost:3000/setup` e siga o wizard:

1. Super Admin (não gerenciável depois)
2. Settings (DNS aprovados, limiar online…)
3. Servidor ACS (URL NBI + Bearer — probe server-side)
4. Concluir → login

## Desenvolvimento

```bash
make api-test   # pytest
make web-test   # vitest + tsc
make test
```

## Documentação

- [Instalação](docs/instalacao.md)
- [NBI / multi-ACS](docs/nbi.md)
- [Paths vendor/modelo](docs/vendor-paths.md)
- [Device actions](docs/device-actions.md)
- [ACL e Super Admin](docs/acl.md)
- [Criptografia](docs/crypto.md)
- [Design system](docs/design-system.md)
- [CONTRIBUTING](CONTRIBUTING.md)

## Licença

MIT — veja [LICENSE](LICENSE).
