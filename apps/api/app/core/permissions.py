from __future__ import annotations

ALL_PERMISSION_IDS: tuple[str, ...] = (
    "acs.access",
    "acs.devices.write",
    "acs.diagnostic",
    "acs.diagnostic-clear",
    "acs.firmwares",
    "acs.firmwares-upload",
    "acs.firmwares-delete",
    "acs.servers",
    "dashboard.view",
    "security.users",
    "security.groups",
    "settings.view",
    "settings.edit",
)

PERMISSION_MODULES: dict[str, dict] = {
    "acs": {
        "label": "ACS",
        "permissions": [
            {"key": "access", "label": "Acessar ACS"},
            {"key": "devices.write", "label": "Alterar CPE (wifi/wan/dhcp/...)"},
            {"key": "diagnostic", "label": "Rodar diagnóstico"},
            {"key": "diagnostic-clear", "label": "Limpar histórico de diagnóstico"},
            {"key": "firmwares", "label": "Ver firmwares"},
            {"key": "firmwares-upload", "label": "Upload de firmware"},
            {"key": "firmwares-delete", "label": "Remover firmware"},
            {"key": "servers", "label": "Gerir servidores GenieACS"},
        ],
    },
    "dashboard": {
        "label": "Dashboard",
        "permissions": [{"key": "view", "label": "Ver dashboard"}],
    },
    "security": {
        "label": "Segurança",
        "permissions": [
            {"key": "users", "label": "Gerir usuários"},
            {"key": "groups", "label": "Gerir grupos"},
        ],
    },
    "settings": {
        "label": "Configurações",
        "permissions": [
            {"key": "view", "label": "Ver settings"},
            {"key": "edit", "label": "Editar settings"},
        ],
    },
}


def normalize_permissions(raw: list[str] | set[str] | None) -> set[str]:
    allowed = set(ALL_PERMISSION_IDS)
    return {p for p in (raw or []) if p in allowed}


OPERATOR_DEFAULT_PERMISSIONS: list[str] = [
    "acs.access",
    "acs.devices.write",
    "acs.diagnostic",
    "acs.firmwares",
    "dashboard.view",
    "settings.view",
]
