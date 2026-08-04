## Summary
<!-- O que muda e por quê -->

## Test plan
- [ ] `make api-test` / `cd apps/api && pytest`
- [ ] `cd apps/web && npm test && npx tsc --noEmit`
- [ ] Fluxo manual (se UI): wizard / login / devices / diagnóstico

## Checklist
- [ ] Testes unitários para lógica nova (obrigatório)
- [ ] Sem secrets / IPs internos / tokens no diff
- [ ] Docs PT atualizados se mudar comportamento público
- [ ] Permissões ACL consideradas (`acs.*` / `settings.*` / `security.*`)
