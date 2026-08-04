# Design system do Mr9

O Mr9 usa uma linguagem clara, técnica e densa para operação prolongada em NOCs. O layout prioriza leitura, comparação e acesso rápido a ações, sem aparência de painel administrativo genérico.

## Fundamentos

- Tipografia principal: Public Sans.
- Tipografia técnica: IBM Plex Mono, somente para serial, MAC, IP, PPPoE, firmware e paths TR-069.
- Escala: 12 px para metadados; 13 px para controles e tabelas; 14 px para corpo e títulos de módulo; 22 px para títulos de página; 24–30 px para métricas.
- Espaçamento: unidade de 4 px, com gaps usuais de 8, 12, 16 e 24 px.
- Controles: altura de 40 px, radius de 5 px e foco teal visível.
- Painéis: radius de 7 px, borda suave e sombra mínima.

## Cores

- Canvas: `#F3F5F7`.
- Superfície: `#FFFFFF`.
- Superfície secundária: `#F8FAFB`.
- Texto: `#17242D`.
- Texto secundário: `#536570`.
- Teal de identidade e ação: `#087F78`.
- Verde: sucesso e online.
- Âmbar: atenção e degradação.
- Vermelho: falha e offline.
- Azul: informação, nunca ação principal.

Use os tokens declarados em `src/app/globals.css`; não replique hexadecimais nas páginas.

## Composição

- O shell usa topbar clara e navegação horizontal em cinza azulado.
- Topbar, navegação e conteúdo compartilham largura máxima de 1840 px e o mesmo padding responsivo.
- Tabelas usam cabeçalhos fixos, divisórias suaves e hover consistente.
- Configurações ficam em Administração; módulos operacionais permanecem na navegação principal.
- Estados vazios devem explicar a ausência do dado. Dados simulados são permitidos somente em previews isolados.

## Contribuição

Novas páginas devem reutilizar os primitives de `src/components/ops`. Mudanças no shell ficam em `src/components/chrome`. Novos itens de navegação ficam em `src/lib/navigation.ts` e precisam de teste para a regra de estado ativo.
