# ACL — grupos, usuários e Super Admin

Modelo mental alinhado ao MasterOLT:

| Entidade | Função |
|---|---|
| **Super Admin** | Criado só no wizard. `is_superadmin=true`. Sem grupo/role. **Não** listado no CRUD. Bypass total. |
| **Grupo** | Nome + lista de permission keys (`acs.access`, `settings.edit`, …). |
| **Usuário** | E-mail/senha + **um** `group_id`. |

## Catálogo MVP

Ver `apps/api/app/core/permissions.py`.

## Regras de UI

- Tela Usuários filtra `is_superadmin=false`
- Matriz de permissões na tela Grupos
- Rotas usam `auth.require("…")`
