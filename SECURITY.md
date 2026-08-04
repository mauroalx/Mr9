# Segurança

## Versões suportadas

Enquanto o Mr9 estiver em `0.x`, somente a versão mais recente recebe correções de segurança.

## Relatar uma vulnerabilidade

Não abra uma issue pública com tokens, endereços de clientes, inventários TR-069 ou detalhes exploráveis. Use o recurso **Private vulnerability reporting** do repositório no GitHub.

Inclua o impacto, a versão afetada e um procedimento mínimo de reprodução sem dados reais de assinantes. A confirmação inicial será feita em até sete dias.

## Operação segura

- Publique o Mr9 somente atrás de HTTPS.
- Não exponha Postgres nem o NBI do GenieACS à internet.
- Gere os segredos com `./scripts/bootstrap.sh`.
- Restrinja o NBI do GenieACS ao endereço do servidor Mr9.
- Nunca anexe `.env`, tokens JWT, bearer NBI ou inventários completos em issues.
