# Criptografia

| Segredo | Tratamento |
|---|---|
| `MR9_SECRET_KEY` | Env (bootstrap gera). Deriva chave Fernet + assinatura JWT |
| Bearer NBI | Fernet AES em `acs_servers.bearer_token_encrypted` |
| Senhas | Argon2id (passlib) |
| Tráfego | TLS no edge (nginx/caddy) |

Não é full-disk encryption da VPS — recomenda-se LUKS/credenciais de volume no provedor.

Rotação de `MR9_SECRET_KEY` invalida tokens NBI cifrados: será necessário recadastrar Bearers (documente o procedimento na operação).
