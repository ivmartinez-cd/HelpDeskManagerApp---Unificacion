"""Medición Fase 0.3 del refactor de integraciones externas (SOLO LECTURA).

Compara el costo por llamada de las estrategias de concurrencia candidatas
para el cliente zeep de wsAyC:

  (singleton) un Client compartido con su requests.Session — patrón actual de
              insumos; rápido pero Session no es thread-safe documentado.
  (b)         wsdl.Document parseado UNA vez y compartido + Transport/Client
              nuevos por llamada — cada llamada tiene su Session propio.

Usa exclusivamente getTopLiquidations — ninguna operación de escritura.

Uso: uv run python scripts/medir_zeep_document_compartido.py
"""

import statistics
import time

from zeep import Client, Settings
from zeep.transports import Transport
from zeep.wsdl import Document

WSDL_URL = "https://wsg.cdsisa.com.ar/wsAyC_server.php?wsdl"
REAL_ENDPOINT = "https://wsg.cdsisa.com.ar/wsAyC_server.php"
TIMEOUT = 30
EMPRESA_CD_ID = "1303"  # BAHIA — solo lectura, top chico
TOP = "5"
LLAMADAS = 5


def _call(client: Client) -> int:
    client.service._binding_options["address"] = REAL_ENDPOINT
    raw = client.service.getTopLiquidations(
        IdEmpresa=EMPRESA_CD_ID, IdEstado="", OrderBy="", Top=TOP
    )
    return len(raw or "")


def main() -> None:
    t0 = time.perf_counter()
    settings = Settings()
    load_transport = Transport(timeout=TIMEOUT, operation_timeout=TIMEOUT)
    document = Document(WSDL_URL, load_transport, settings=settings)
    t_document = time.perf_counter() - t0
    print(f"Carga+parseo del wsdl.Document (una vez por proceso): {t_document:.3f}s")

    singleton = Client(document, transport=load_transport, settings=settings)
    _call(singleton)  # warm-up de conexión

    tiempos_singleton: list[float] = []
    for _ in range(LLAMADAS):
        t0 = time.perf_counter()
        _call(singleton)
        tiempos_singleton.append(time.perf_counter() - t0)

    tiempos_por_llamada: list[float] = []
    for _ in range(LLAMADAS):
        t0 = time.perf_counter()
        transport = Transport(timeout=TIMEOUT, operation_timeout=TIMEOUT)
        client = Client(document, transport=transport, settings=settings)
        _call(client)
        tiempos_por_llamada.append(time.perf_counter() - t0)

    print(
        f"(singleton) Client+Session compartidos: "
        f"mediana {statistics.median(tiempos_singleton):.3f}s "
        f"({['%.3f' % t for t in tiempos_singleton]})"
    )
    print(
        f"(b) Document compartido + Transport/Client por llamada: "
        f"mediana {statistics.median(tiempos_por_llamada):.3f}s "
        f"({['%.3f' % t for t in tiempos_por_llamada]})"
    )


if __name__ == "__main__":
    main()
