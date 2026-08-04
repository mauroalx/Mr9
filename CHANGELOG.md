# Changelog

## 0.1.0 — 2026-08-04

Primeiro MVP open source do Mr9:

- Wizard `/setup` com Super Admin, settings (DNS/limiar) e 1º ACS (NBI + Bearer cifrado)
- ACL grupo → usuário; Super Admin fora do CRUD
- Multi-GenieACS somente no backend; inventário e workbench (Wi-Fi/WAN/DHCP/hosts/portmap/ferramentas/diagnóstico)
- Diagnóstico scored settings-driven + histórico; neighbors ZTE/Huawei/Intelbras
- Dashboard com contagem total no NBI, KPIs e séries operacionais
- Telemetria WAN em tempo real, interfaces LAN e dados ópticos quando reportados
- Gestão de usuários, grupos, ACS, tarefas e auditoria
- Catálogo de firmwares e tarefas operacionais GenieACS
- Migração inicial Alembic e imagens Docker sem usuário root
- CI GitHub Actions (ruff/pytest + eslint/tsc/vitest); templates issue/PR; docs PT
