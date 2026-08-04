# Criptografia

| Segredo | Tratamento |
|---|---|
| `MR9_SECRET_KEY` | Env (bootstrap gera). Deriva chave Fernet + assinatura JWT |
| Bearer NBI | Opcional. Se presente: Fernet AES em `acs_servers.bearer_token_encrypted`. Ausente = NBI sem `Authorization`. |
| Senhas | Argon2id (passlib) |
| Tráfego | TLS no edge (nginx/caddy) |

Não é full-disk encryption da VPS — recomenda-se LUKS/credenciais de volume no provedor.

## Fingerprint e integridade

Ao cifrar um bearer NBI (wizard, create ou PATCH), o Mr9 grava `app_settings.crypto_key_fp` (16 hex da SHA-256 da `MR9_SECRET_KEY`).

Na subida da API e em `GET /api/v1/health` → `crypto`:

- detecta placeholders/fragilidade da chave;
- compara fingerprint armazenada vs atual;
- tenta decifrar cada servidor ACS e lista `servers_unreadable`.

Se o decrypt falhar, as rotas ACS respondem **503** com mensagem acionável (não 500 opaco).

`GET /acs/servers` inclui `credentials_ok` para a UI marcar servidores ilegíveis.

## Rotação / recuperação

Rotacionar `MR9_SECRET_KEY` **invalida** JWT e bearers cifrados.

Procedimento:

1. Defina a nova chave no `.env` (nunca use o placeholder do `.env.example`).
2. Reinicie a API.
3. Faça login de novo (JWT antigo inválido).
4. Em **Settings → Servidores ACS**, regrave o bearer NBI (`PATCH /acs/servers/{id}` com `bearer_token`) **ou** remova a auth se o NBI não exige (`bearer_token: ""`).
5. Health deve mostrar `crypto.ok: true`.

Se ainda tiver a chave antiga e quiser evitar regravar tokens: restaure-a no `.env` e reinicie.
