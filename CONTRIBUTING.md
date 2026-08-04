# Contribuindo com o Mr9

Obrigado por contribuir. O projeto prioriza **ISPs reais**, código limpo e PRs pequenas.

## Definition of Done

1. `ruff check` + `pytest` em `apps/api` verdes
2. `tsc --noEmit` + `npm test` + `npm run lint` em `apps/web` verdes
3. **Teste unitário obrigatório** para lógica nova (crypto, ACL, diagnóstico, client NBI, mappers)
4. Template de PR preenchido
5. Sem secrets / IPs privados de operadoras no diff
6. Docs PT se mudar comportamento do wizard, ACL ou NBI

## Como rodar testes

```bash
# API
cd apps/api
python3 -m pip install -r requirements.txt
MR9_SECRET_KEY=dev PYTHONPATH=. pytest -q

# Web
cd apps/web
npm ci
npm test
npx tsc --noEmit
```

## Adicionar permission key

1. Inclua em `apps/api/app/core/permissions.py` (`ALL_PERMISSION_IDS` + `PERMISSION_MODULES`)
2. Use `auth.require("modulo.chave")` na rota **ou** `permission=` no `@action(...)`
3. Adicione teste cobrindo 403 sem a permissão (quando houver fixture de usuário comum)

## Adicionar device action

1. Handler em `apps/api/app/acs/actions/<area>.py` com `@action("nome", permission=..., notes=...)`
2. Se for arquivo novo: importe-o em `apps/api/app/acs/actions/__init__.py`
3. Atualize `tests/test_acs_actions_registry.py`
4. Guia: [docs/device-actions.md](docs/device-actions.md)

## Adicionar path vendor (Wi‑Fi / vizinhança / WAN…)

1. Abra issue com template **Vendor path**
2. Configure o path em `apps/api/app/cpe/profiles/` — **não** espalhe `if manufacturer ==` no código de rotas
3. Ordem: perfil de **modelo** → **vendor** → **generic** (ver [docs/vendor-paths.md](docs/vendor-paths.md))
4. Teste unitário com inventário JSON mínimo (`test_cpe_params_registry` / `test_cpe_extract`)
5. Documente o path em `docs/nbi.md`

## Escopos de PR bons

- Um vendor / um bug / uma tela
- Evite monólitos de 3k linhas — prefira módulos
