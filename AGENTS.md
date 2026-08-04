# AGENTS.md — guia para agentes / automações

- Responda e documente em **português** quando o alvo for docs do repo.
- Nunca coloque tokens NBI, `MR9_SECRET_KEY` ou IPs de clientes no código.
- Chamadas GenieACS **somente** em `apps/api` via `GenieAcsClient` + `build_client`.
- Super Admin: `is_superadmin=true`, sem grupo, fora do CRUD.
- Settings (DNS etc.) vêm de `AppSettings`, nunca hard-code de operadora.
- Antes de PR: rode a suíte de testes; CI falha sem unitários relevantes.
- Não edite planos em `.cursor/plans` a menos que o humano peça.
