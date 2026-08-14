"""Script de diagnóstico de solo lectura: literales reales del campo Estado en getTopLiquidations.

Corre desde el contenedor:
  docker exec helpdesk-manager-backend uv run python scripts/inspect_estado_soap.py
"""
import collections
import json

from zeep import Client
from zeep.transports import Transport

WSDL = "https://wsg.cdsisa.com.ar/wsAyC_server.php?wsdl"
ENDPOINT = "https://wsg.cdsisa.com.ar/wsAyC_server.php"

# IDs de empresas a probar (solo lectura — getTopLiquidations)
EMPRESAS = [
    (137, "PENTACOM"),
    (600, "SUPERNOVA"),
    (504, "GESTION INTEGRAL"),
    (740, "INFOMAC"),
]

transport = Transport(timeout=30, operation_timeout=30)
client = Client(WSDL, transport=transport)
client.service._binding_options["address"] = ENDPOINT

freq_global: dict[str, int] = collections.Counter()

for empresa_id, nombre in EMPRESAS:
    raw = client.service.getTopLiquidations(
        IdEmpresa=str(empresa_id), IdEstado="", OrderBy="", Top="50"
    )
    items = json.loads(raw) if raw else []
    freq_local: dict[str, int] = collections.Counter()
    for item in items:
        liq = item.get("Liquidation", item)
        e = liq.get("Estado", "(sin campo)")
        freq_local[e] += 1
        freq_global[e] += 1
    print(f"\nEmpresa {empresa_id} ({nombre}), n={len(items)}")
    for estado, cnt in sorted(freq_local.items(), key=lambda x: -x[1]):
        print(f"  Estado={estado!r:<25}  freq={cnt}")

print("\n=== FRECUENCIA GLOBAL (4 prestadores) ===")
for estado, cnt in sorted(freq_global.items(), key=lambda x: -x[1]):
    print(f"  Estado={estado!r:<25}  freq={cnt}")

print("\n=== CAMPOS DEL PRIMER ITEM DE PENTACOM ===")
raw = client.service.getTopLiquidations(
    IdEmpresa="137", IdEstado="", OrderBy="", Top="1"
)
items = json.loads(raw) if raw else []
if items:
    first = items[0].get("Liquidation", items[0])
    for k, v in first.items():
        print(f"  {k}: {v!r}")

print("\nDone.")
