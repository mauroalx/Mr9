# Device actions

## Problema que resolvemos

A rota `POST /acs/devices/{id}/actions` **não** deve virar um `if action == …` de 300 linhas.
Cada ação é um handler registrado.

## Onde mexer

| Camada | Path |
|---|---|
| Rota fina | `apps/api/app/api/routes/devices.py` |
| Dispatch / `@action` | `apps/api/app/acs/actions/base.py` |
| Handlers | `apps/api/app/acs/actions/*.py` (`wifi`, `wan`, `dhcp`, …) |
| Paths TR-069 | `apps/api/app/cpe/profiles/` (não misturar com actions) |
| Resumo / workbench | `apps/api/app/acs/summary.py` |

## Adicionar uma action

```python
# apps/api/app/acs/actions/meu_modulo.py
from app.acs.actions.base import ActionContext, action

@action("minha_acao", permission="acs.devices.write", notes="O que faz")
async def minha_acao(ctx: ActionContext) -> dict:
    # ctx.client, ctx.device_id, ctx.params, ctx.db, ctx.auth, ctx.server
    return {"ok": True}
```

1. Crie o handler com `@action(...)`.
2. Garanta o import em `ensure_handlers_loaded()` em `base.py` (já importa os pacotes listados).
3. Se for módulo novo, acrescente o import em `base.ensure_handlers_loaded`.
4. Teste: registre o nome em `tests/test_acs_actions_registry.py`.
5. Paths vendor → `docs/vendor-paths.md`, não hard-code no handler.

Catálogo runtime: `GET /api/v1/acs/actions` (precisa `acs.access`).
