# NBI GenieACS e multi-ACS

## Princípio

O frontend envia apenas `X-Acs-Server-Id` + JWT. A API:

1. Carrega `AcsServer`
2. Decifra `bearer_token_encrypted`
3. Chama o NBI (`/devices`, `/tasks`, …)

## Cadastro

Campos: `name`, `base_url`, `bearer_token`, `verify_tls`, `online_threshold_s`, `is_default`.

Probe: `GET {base}/devices/?query={}&limit=1` com Bearer.

## Firewall

No GenieACS/ACL de rede, libere **somente** o IP da VPS Mr9. Técnicos no browser não precisam de rota até `:7557`.

## Compatibilidade conhecida (herdada do MasterOLT)

| Família | Path / trigger |
|---|---|
| ZTE H3601P P1/P3 | `LANDevice.1.WIFI.Radio.*.DiagnosticsState` |
| ZTE H3601P P9/P10 | `LANDevice.1.WiFi.Radio.*.DiagnosticsState` (case) |
| Huawei EG8145 / K562e | `LANDevice.1.WiFi.NeighboringWiFiDiagnostic` |
| Intelbras GF1200 / W4 | `InternetGatewayDevice.WiFi.X_ITBS_StartNeighboringWiFiDiagnostic` |

Leaf stub GenieACS sem `_value` ainda pode exigir cuidado em plans de scan — PRs bem-vindas.
