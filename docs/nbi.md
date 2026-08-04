# NBI GenieACS e multi-ACS

## Princípio

O frontend envia apenas `X-Acs-Server-Id` + JWT. A API:

1. Carrega `AcsServer`
2. Se houver `bearer_token_encrypted`, decifra; senão chama o NBI sem auth
3. Chama o NBI (`/devices`, `/tasks`, …)

## Cadastro

Campos: `name`, `base_url`, `bearer_token` (**opcional**), `verify_tls`, `online_threshold_s`, `is_default`.

Sem bearer: o client chama o NBI sem `Authorization` (cenário típico com GenieACS aberto só ao IP da VPS Mr9).

Com bearer: valor é cifrado em `bearer_token_encrypted`; omitido/vazio no PATCH remove a auth.

Probe: `GET {base}/devices/?query={}&limit=1` (com Bearer se configurado).

## Firewall

No GenieACS/ACL de rede, libere **somente** o IP da VPS Mr9. Técnicos no browser não precisam de rota até `:7557`.

## Compatibilidade conhecida (catálogo `app/cpe/profiles`)

| Família | Path / trigger | Perfil |
|---|---|---|
| Genérico IGD | `LANHostConfigManagement`, `WLANConfiguration`, `IPPingDiagnostics` | `generic.igd` |
| ZTE H3601P P9/P10 | `LANDevice.1.WiFi.Radio.*.NeighboringWiFiDiagnostic` | `zte.h3601p` |
| ZTE H3601P P1/P3 | `LANDevice.1.WIFI.Radio.*` (case) | `zte` / fallback H3601 |
| Huawei EG8145 / K562e | `…WiFi.NeighboringWiFiDiagnostic` | `huawei.eg8145` |
| Intelbras GF1200 / W4 | `WiFi.X_ITBS_StartNeighboringWiFiDiagnostic` + `…Result` | `intelbras.gf1200` |

Guia completo para contribuir paths: [vendor-paths.md](vendor-paths.md).

Leaf stub GenieACS sem `_value`: use `param_exists(..., require_value=False)` em `app/cpe/tree.py`.
