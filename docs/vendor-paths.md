# Paths TR-069 por vendor / modelo

## Onde configurar

| O quê | Onde |
|---|---|
| Capabilidades (`wifi.ssid`, `neighbor.result`, …) | `apps/api/app/cpe/params.py` → `Cap` |
| Helpers de árvore Genie (`_value`, dig) | `apps/api/app/cpe/tree.py` |
| Perfil **genérico** (fallback) | `apps/api/app/cpe/profiles/generic.py` |
| Perfis **ZTE / Huawei / Intelbras** | `apps/api/app/cpe/profiles/<vendor>.py` |
| Registro (concatena perfis) | `apps/api/app/cpe/profiles/__init__.py` |
| Extração (usa o catálogo) | `apps/api/app/cpe/extract.py` |

## Ordem de resolução

1. Perfil de **modelo** (`product_class` + manufacturer) — `priority` baixa (ex.: 10)
2. Perfil de **vendor** (todos os modelos) — `priority` média (ex.: 100)
3. Perfil **generic.igd** — `priority` 1000

Para uma capacidade (`Cap.NEIGHBOR_RESULT`, etc.), os candidatos são unidos **nessa ordem**, sem duplicar. Na árvore do CPE, o **primeiro path que existir** vence.

Não dá para catalogar todos os ONUs do mundo: o genérico cobre TR-098; vendors específicos sobrescrevem o que importa.

## Adicionar path / modelo

1. Abra issue com template **Vendor path** (vendor, ProductClass, path, leaf).
2. Preferência: estender o `VendorProfile` do vendor; se for quirks de um modelo, crie um perfil `vendor.modelo` com `priority=10` e só as families que diferem.
3. Preencha `notes` na `PathFamily` (o que o path faz / firmware).
4. Teste unitário em `tests/test_cpe_params_registry.py` e, se for extract, inventário JSON mínimo em `tests/test_cpe_extract.py`.
5. Documente uma linha na tabela de `docs/nbi.md`.

Debug útil:

```python
from app.cpe.profiles import describe_resolution, Cap
print(describe_resolution(device_dict, Cap.NEIGHBOR_RESULT))
```

## Exemplo mínimo

```python
# apps/api/app/cpe/profiles/meu_vendor.py
from app.cpe.params import Cap, PathFamily, VendorProfile

MEU_MODELO = VendorProfile(
    id="acme.x1",
    manufacturers=frozenset({"acme"}),
    product_classes=frozenset({"x1"}),
    priority=10,
    notes="ONU Acme X1 — scan vizinho sob LANDevice.1.WiFi",
    families={
        Cap.NEIGHBOR_RESULT: PathFamily(
            capability=Cap.NEIGHBOR_RESULT,
            candidates=("InternetGatewayDevice.LANDevice.1.WiFi.NeighboringWiFiDiagnostic.Result",),
            leaf_map={"ssid": ("SSID",), "channel": ("Channel",), "rssi": ("SignalStrength",)},
            notes="Resultado após DiagnosticsState=Requested",
        ),
    },
)

PROFILES = (MEU_MODELO,)
```

Depois importe `PROFILES` em `apps/api/app/cpe/profiles/__init__.py` dentro de `ALL_PROFILES`.
