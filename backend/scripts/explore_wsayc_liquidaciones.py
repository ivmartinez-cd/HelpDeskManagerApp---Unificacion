"""Fase 1 de MASTER_PROMPT_AUTOMATIZACION_FUENTES_LIQUIDACIONES.md — sondeo wsAyC.

Solo operaciones de LECTURA (get*) del WSDL real; ninguna operación persist*/void*/
set*/change*. Respuestas JSON-en-string (mismo contrato que usa insumos, ver
wsayc_parsing.safe_parse). Imprime claves y una muestra truncada por operación para
mapear qué campos expone cada una.

Uso (dentro del contenedor backend, con `uv`):
    uv run python scripts/explore_wsayc_liquidaciones.py
"""

import json
from typing import Any

from zeep import Client
from zeep.transports import Transport

from src.modules.insumos.infrastructure.soap.zeep_wsayc_gateway import REAL_ENDPOINT, WSDL_URL

_PENTACOM_SIGES_ID = "137"  # dbo.Empresa 'PST Cordoba - Pentacom S.A.'
_LIQ_ID_REAL = "3876"  # local '3876-6' (PENTACOM), verificada en el port


def _resumir(nombre: str, crudo: object) -> None:
    print(f"\n=== {nombre} ===")
    if crudo is None:
        print("  respuesta None")
        return
    try:
        datos: Any = json.loads(str(crudo))
    except (json.JSONDecodeError, TypeError):
        print(f"  no-JSON: {str(crudo)[:300]!r}")
        return
    if isinstance(datos, list):
        print(f"  lista de {len(datos)} item(s)")
        for item in datos[:2]:
            print(f"  item: {json.dumps(item, ensure_ascii=False)[:450]}")
    elif isinstance(datos, dict):
        print(f"  dict con claves {list(datos.keys())}")
        print(f"  {json.dumps(datos, ensure_ascii=False)[:600]}")
    else:
        print(f"  escalar: {datos!r}")


def main() -> None:
    client = Client(WSDL_URL, transport=Transport(timeout=30))
    client.service._binding_options["address"] = REAL_ENDPOINT
    service = client.service

    _resumir("getTechnicians(tipoTecnico='')", service.getTechnicians(""))
    _resumir(
        f"getEmpresasPrestador(usuario_id={_PENTACOM_SIGES_ID})",
        service.getEmpresasPrestador(_PENTACOM_SIGES_ID),
    )
    _resumir(f"getLiquidationById(id={_LIQ_ID_REAL})", service.getLiquidationById(_LIQ_ID_REAL))
    _resumir(
        f"getLiquidationResume(id={_LIQ_ID_REAL})", service.getLiquidationResume(_LIQ_ID_REAL)
    )
    _resumir(
        f"getLiquidationDetails(nro={_LIQ_ID_REAL})", service.getLiquidationDetails(_LIQ_ID_REAL)
    )
    _resumir(
        f"getPayableIncidents(IdUsuario={_PENTACOM_SIGES_ID})",
        service.getPayableIncidents(_PENTACOM_SIGES_ID),
    )
    _resumir(
        f"getTopLiquidations(IdEmpresa={_PENTACOM_SIGES_ID}, Top=2)",
        service.getTopLiquidations(_PENTACOM_SIGES_ID, "", "", "2"),
    )


if __name__ == "__main__":
    main()
