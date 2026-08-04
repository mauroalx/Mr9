# Paths TR-069 por vendor / modelo

## Camadas (não misturar)

| Camada | Responsabilidade |
|---|---|
| `app/cpe/tree.py` | Única fonte de `leaf` / `dig` / `param_at` |
| `app/cpe/params.py` + `profiles/` | Paths TR-069 (Cap + vendor/modelo → generic) |
| `app/cpe/extract.py` | Ler inventário Genie usando o catálogo |
| `app/cpe/traffic.py` | Selecionar a WAN principal e normalizar contadores acumulados |
| `app/acs/actions/` | Side-effects NBI (`@action`); usar `ctx.load_device()`, `task_result`, Caps — **sem** string de path solta |
| `app/services/diagnostic_service.py` | Score; consome extract/catálogo, não dig hardcoded |

Debug: `describe_resolution(device_dict, Cap.NEIGHBOR_RESULT)` (ver bloco abaixo).

## Ordem de resolução

1. Perfil de **modelo** (`product_class` + manufacturer) — `priority` baixa (ex.: 10)
2. Perfil de **vendor** (todos os modelos) — `priority` média (ex.: 100)
3. Perfil **generic.igd** — `priority` 1000

Para uma capacidade (`Cap.NEIGHBOR_RESULT`, etc.), os candidatos são unidos **nessa ordem**, sem duplicar. Na árvore do CPE, o **primeiro path que existir** vence.

Não dá para catalogar todos os ONUs do mundo: o genérico cobre TR-098; vendors específicos sobrescrevem o que importa.

## Contadores de tráfego WAN

`Cap.WAN_BYTES_RECEIVED` e `Cap.WAN_BYTES_SENT` resolvem, nesta ordem, os
contadores da conexão, os agregados de `WANDevice` e os contadores da interface
Ethernet. O cálculo de taxa nunca pertence ao perfil: ele usa duas amostras
normalizadas e o tempo realmente decorrido.

No TR-181, `Cap.WAN_TRAFFIC_INTERFACE` procura interfaces PPP, IP, Ethernet,
PTM, ATM e ópticas e lê `Stats.BytesReceived/BytesSent`. A amostra carrega o
timestamp real do leaf; chamadas ao NBI sem avanço desse timestamp não geram
pontos no gráfico.

Uma contribuição de vendor deve incluir um inventário mínimo que prove os dois
contadores. Metadados GenieACS sem `_value` não são valores válidos. Se o
contador atual for menor que o anterior, o frontend considera reset ou overflow
e descarta o ponto em vez de desenhar um pico.

## Telemetria óptica da ONU

`Cap.OPTICAL_CONTAINER` detecta interfaces ópticas sem acoplar a rota ao
fabricante. O workbench normaliza apenas o contrato de apresentação: tecnologia,
status, RX/TX, distância, temperatura, tensão, bias e contadores FEC/HEC/CRC.
O path de origem nunca é devolvido ao frontend.

Compatibilidade inicial:

| Perfil | Containers |
|---|---|
| Huawei | `X_GponInterafceConfig` (typo presente em firmware) e `X_GponInterfaceConfig` |
| Genérico | `Device.Optical.Interface.{i}` e `InternetGatewayDevice.WANDevice.1.OpticalInterface.{i}` |

Um stub GenieACS sem `_value` não detecta uma ONU nem vira texto na tela. O
extrator também não tenta corrigir escalas proprietárias por heurística: se um
vendor transmite potência, tensão ou distância em unidade codificada, a
conversão deve entrar no perfil desse vendor acompanhada de fixture real.

FEC, HEC e CRC são contadores acumulados. Um total isolado é inventário; somente
o delta positivo entre amostras pode representar erro atual e afetar diagnóstico.

## Adicionar path / modelo

1. Abra issue com template **Vendor path** (vendor, ProductClass, path, leaf).
2. Preferência: estender o `VendorProfile` do vendor; se for quirks de um modelo, crie um perfil `vendor.modelo` com `priority=10` e só as families que diferem.
3. Preencha `notes` na `PathFamily` (o que o path faz / firmware).
4. Teste unitário em `tests/test_cpe_params_registry.py` e, se for extract, inventário JSON mínimo em `tests/test_cpe_extract.py`.
5. Documente uma linha na tabela de `docs/nbi.md`.

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
