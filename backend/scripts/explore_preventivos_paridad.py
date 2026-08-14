"""Paridad de "preventivos por zona" entre la réplica SiGesReadOnly y el
MERCURIO productivo vía wsAyC (SOLO lecturas SOAP: getMachineBySerial +
getMachineIncidents — nada de persist*/void*).

Para cada caso de la zona SUR (ronda 3): corre la consulta productiva del
módulo contra la réplica y busca el mismo incidente preventivo en wsAyC,
comparando número, estado y fecha de cierre.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_preventivos_paridad.py
"""

import asyncio

import pyodbc

from src.modules.insumos.infrastructure.soap.zeep_wsayc_gateway import ZeepWsAycGateway
from src.modules.preventivos.infrastructure.siges.query import PARQUE_ZONA_SQL
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 60

# (serie, id_maquina, nro_incidente esperado) — casos reales de la ronda 3.
_CASOS = [
    ("ZELLBJEJ400020A", 31852, "842633"),
    ("07QWB9UG3A005LX", 20329, "842630"),
    ("076UBJFH30002MT", 30077, "842708"),
]


def _replica_por_maquina() -> dict[int, tuple[str, str, object, object]]:
    settings = get_settings()
    conn = pyodbc.connect(
        build_mercurio_connection_string(settings), timeout=_TIMEOUT_SECONDS, autocommit=True
    )
    try:
        conn.timeout = _TIMEOUT_SECONDS
        cursor = conn.cursor()
        cursor.execute(PARQUE_ZONA_SQL, "SUR")
        filas = {}
        for row in cursor.fetchall():
            filas[int(row.id_maquina)] = (
                row.serie.strip(),
                row.cliente.strip(),
                row.frecuencia_dias,
                row.fecha_ultimo_preventivo,
            )
        return filas
    finally:
        conn.close()


async def _wsayc(serie: str, nro_esperado: str) -> None:
    gw = ZeepWsAycGateway()
    machine = await gw.get_machine_by_serial(serie)
    if machine is None:
        print(f"  wsAyC: {serie} sin asignar / no encontrada")
        return
    incidentes = await gw.get_machine_incidents(machine.machine_id, top=10)
    match = next((i for i in incidentes if i.numero == nro_esperado), None)
    if match is None:
        vistos = [(i.numero, i.estado, i.fecha) for i in incidentes]
        print(f"  wsAyC: incidente {nro_esperado} NO está en el top 10: {vistos}")
        return
    print(
        f"  wsAyC: incidente {match.numero} estado={match.estado!r} "
        f"fecha={match.fecha!r} cierre={match.fecha_cierre!r} tecnico={match.tecnico!r}"
    )


async def main() -> None:
    replica = _replica_por_maquina()
    for serie, id_maquina, nro_esperado in _CASOS:
        print(f"\n=== {serie} (ID_Maquina {id_maquina}) ===")
        fila = replica.get(id_maquina)
        if fila is None:
            print("  réplica: NO aparece en la consulta de zona SUR")
        else:
            print(
                f"  réplica: cliente={fila[1]!r} frecuencia={fila[2]} "
                f"ultimo_preventivo={fila[3]}"
            )
        await _wsayc(serie, nro_esperado)


if __name__ == "__main__":
    asyncio.run(main())
