# Frontend do Mr9

Interface operacional do Mr9, construída com Next.js, React, TypeScript e Tailwind CSS.

## Desenvolvimento

```bash
npm install
npm run dev
```

Por padrão, a aplicação usa `http://localhost:8000/api/v1`. Defina `NEXT_PUBLIC_API_BASE_URL` para apontar para outra API.

## Estrutura

- `src/app`: rotas e composição das páginas.
- `src/components/chrome`: cabeçalho e navegação globais.
- `src/components/ops`: componentes compartilhados da interface operacional.
- `src/lib/api.ts`: único cliente HTTP usado pelo frontend.
- `src/lib/navigation.ts`: catálogo da navegação principal e regra de estado ativo.

## Criando uma página

1. Crie a rota no grupo `src/app/(app)` para herdar autenticação e o shell operacional.
2. Use `PageHead`, `Panel`, `PanelTitle`, `Btn`, `Control` e os demais primitives de `src/components/ops`.
3. Faça integrações por `api()`; componentes puramente visuais não devem executar requisições.
4. Adicione o módulo em `src/lib/navigation.ts` somente quando a rota estiver acessível.
5. Não use dados simulados em rotas do core. Estados sem contrato devem explicar claramente a indisponibilidade.

## Permissões e traduções

O catálogo de permissões fica em `src/lib/permissions-meta.ts` e deve acompanhar as permissões definidas pela API. Novos textos devem nascer em português claro e permanecer centralizáveis para a futura camada de internacionalização.

## Qualidade

Antes de enviar um PR:

```bash
npm run test
npx eslint src
npx tsc --noEmit --incremental false
npm run build
```

Inclua testes unitários para regras de navegação, formatação, transformação de dados e estados críticos. Preserve contratos da API e não introduza chamadas diretas ao GenieACS no navegador.
