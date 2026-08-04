export type PermissionMeta = {
  id: string;
  module: string;
  moduleLabel: string;
  label: string;
  description: string;
  level: "leitura" | "escrita" | "admin";
};

export const PERMISSION_CATALOG: PermissionMeta[] = [
  {
    id: "acs.access",
    module: "acs",
    moduleLabel: "ACS",
    label: "Acesso ao inventário",
    description: "Listar e abrir dispositivos",
    level: "leitura",
  },
  {
    id: "acs.devices.write",
    module: "acs",
    moduleLabel: "ACS",
    label: "Alterar CPE",
    description: "Wi-Fi, WAN, DHCP e ações de escrita",
    level: "escrita",
  },
  {
    id: "acs.diagnostic",
    module: "acs",
    moduleLabel: "ACS",
    label: "Diagnóstico",
    description: "Executar ping, traceroute e scores",
    level: "escrita",
  },
  {
    id: "acs.diagnostic-clear",
    module: "acs",
    moduleLabel: "ACS",
    label: "Limpar diagnósticos",
    description: "Apagar histórico de diagnóstico",
    level: "admin",
  },
  {
    id: "acs.firmwares",
    module: "acs",
    moduleLabel: "ACS",
    label: "Ver firmwares",
    description: "Consultar catálogo de imagens",
    level: "leitura",
  },
  {
    id: "acs.firmwares-upload",
    module: "acs",
    moduleLabel: "ACS",
    label: "Upload de firmware",
    description: "Enviar novas imagens",
    level: "escrita",
  },
  {
    id: "acs.firmwares-delete",
    module: "acs",
    moduleLabel: "ACS",
    label: "Remover firmware",
    description: "Excluir imagens do catálogo",
    level: "admin",
  },
  {
    id: "acs.servers",
    module: "acs",
    moduleLabel: "ACS",
    label: "Servidores ACS",
    description: "Cadastrar e testar GenieACS",
    level: "admin",
  },
  {
    id: "dashboard.view",
    module: "dashboard",
    moduleLabel: "Dashboard",
    label: "Ver dashboard",
    description: "Indicadores e visão geral",
    level: "leitura",
  },
  {
    id: "security.users",
    module: "security",
    moduleLabel: "Segurança",
    label: "Usuários",
    description: "Criar e gerir usuários",
    level: "admin",
  },
  {
    id: "security.groups",
    module: "security",
    moduleLabel: "Segurança",
    label: "Grupos",
    description: "Perfis e permissões",
    level: "admin",
  },
  {
    id: "settings.view",
    module: "settings",
    moduleLabel: "Sistema",
    label: "Ver configurações",
    description: "Consultar parâmetros globais",
    level: "leitura",
  },
  {
    id: "settings.edit",
    module: "settings",
    moduleLabel: "Sistema",
    label: "Editar configurações",
    description: "Alterar DNS, limiares e opções",
    level: "admin",
  },
];

export function permissionsByModule() {
  const map = new Map<string, { label: string; items: PermissionMeta[] }>();
  for (const p of PERMISSION_CATALOG) {
    if (!map.has(p.module)) map.set(p.module, { label: p.moduleLabel, items: [] });
    map.get(p.module)!.items.push(p);
  }
  return [...map.entries()].map(([id, v]) => ({ id, ...v }));
}
