# Mr9

Painel open source para operação de CPEs através do **GenieACS NBI**. O Mr9 reúne inventário, gestão de Wi-Fi/WAN/LAN, tarefas, firmwares, diagnóstico e uma visão NOC para ambientes com um ou mais servidores ACS.

> O navegador se comunica somente com a API Mr9. Bearers NBI permanecem cifrados no backend e nunca são enviados ao frontend.

## Recursos do MVP

- Dashboard com contagem real da frota, disponibilidade, informs, fabricantes e firmwares.
- Inventário paginado com busca por serial, IP, PPPoE, modelo e parâmetros WAN.
- Workbench do CPE: Wi-Fi, WAN, DHCP, hosts, portas, port mapping e telemetria.
- Ping e traceroute por sessão CWMP imediata.
- Tarefas GenieACS, catálogo de firmwares, auditoria e multi-ACS.
- ACL por grupos; o Super Admin fica fora do CRUD comum.
- Perfis TR-069 por modelo → vendor → fallback genérico.

## Arquitetura

- **Web:** Next.js 16, React 19, Tailwind CSS e Recharts.
- **API:** FastAPI, SQLAlchemy e Alembic.
- **Banco:** PostgreSQL 16.
- **Integração:** GenieACS NBI HTTP, exclusivamente pelo backend.

## Instalação rápida

Requisitos: Docker, Docker Compose e um domínio com HTTPS.

```bash
git clone https://github.com/mauroalx/Mr9.git
cd Mr9
cp .env.example .env
./scripts/bootstrap.sh
```

Antes de iniciar em produção, ajuste `MR9_CORS_ORIGINS` no `.env` com a origem HTTPS pública. Depois:

```bash
docker compose up -d --build
```

Use o proxy reverso de [`deploy/nginx.sample.conf`](deploy/nginx.sample.conf), acesse `/setup` e conclua o wizard. Postgres e API ficam vinculados ao host local por padrão; publique somente o proxy HTTPS.

## Desenvolvimento e testes

```bash
docker compose -f docker-compose.dev.yml up -d --build
make test
```

O checklist completo para PRs está em [CONTRIBUTING.md](CONTRIBUTING.md).

## Atualizações e banco

O schema é versionado por Alembic. Faça backup do volume PostgreSQL e execute `alembic upgrade head` antes de iniciar uma nova versão. A imagem oficial do backend executa essa etapa automaticamente.

Instalações locais criadas antes da primeira release pública devem consultar a seção de migração em [docs/instalacao.md](docs/instalacao.md).

## Documentação

- [Instalação e atualização](docs/instalacao.md)
- [NBI e multi-ACS](docs/nbi.md)
- [Perfis vendor/modelo](docs/vendor-paths.md)
- [Device actions](docs/device-actions.md)
- [ACL e Super Admin](docs/acl.md)
- [Criptografia](docs/crypto.md)
- [Design system](docs/design-system.md)
- [Política de segurança](SECURITY.md)

## Limitações conhecidas

TR-069 varia por fabricante e firmware. Recursos não reportados pelo CPE permanecem indisponíveis; novos paths devem entrar no catálogo com fixture e teste. Consulte [docs/vendor-paths.md](docs/vendor-paths.md).

## Licença

MIT — veja [LICENSE](LICENSE).
