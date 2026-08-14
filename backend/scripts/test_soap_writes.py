"""Verificación de las operaciones de escritura SOAP de wsAyC para liquidaciones.

Uso:
  # Paso 1: Observar la liquidación de prueba
  docker exec helpdesk-manager-backend uv run python scripts/test_soap_writes.py \
      --numero 3950-4 --accion observar

  # Paso 2: Aprobar
  docker exec helpdesk-manager-backend uv run python scripts/test_soap_writes.py \
      --numero 3950-4 --accion aprobar

  # Paso 3: Anular (también elimina de la DB local si existe)
  docker exec helpdesk-manager-backend uv run python scripts/test_soap_writes.py \
      --numero 3950-4 --accion anular

  # Consultar estado actual en AyC (solo lectura):
  docker exec helpdesk-manager-backend uv run python scripts/test_soap_writes.py \
      --numero 3950-4 --accion consultar

Notas:
  - El --usuario se manda a wsAyC para auditoría. Default: "Test HelpDesk".
  - El script NO toca otras liquidaciones: opera solo sobre el --numero indicado.
  - Ante cualquier duda, usar --accion consultar antes de escribir.
"""

import argparse
import asyncio
import logging
import os
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from src.modules.liquidaciones.infrastructure.soap.zeep_cd_liquidaciones_gateway import (
    ZeepCdLiquidacionesGateway,
)
from src.modules.liquidaciones.domain.services.numeracion_ayc import numero_liquidacion

logging.basicConfig(level=logging.WARNING)  # silencia zeep salvo errores

DATABASE_URL = os.environ["DATABASE_URL"].replace("postgresql://", "postgresql+asyncpg://", 1)


def _parse_ayc_id(numero: str) -> int:
    return int(numero.split("-")[0])


async def consultar(gw: ZeepCdLiquidacionesGateway, ayc_id: int) -> None:
    print(f"\n[CONSULTAR] Buscando id={ayc_id} en getTopLiquidations...")
    # Busca en el pool de todos los prestadores sería muy lento;
    # el script necesita saber el cd_prestador_id — ver abajo si falla.
    print("  Nota: consultar requiere el cd_prestador_id del prestador.")
    print("  Para Pentacom (cd_id=137):")
    liqs = await gw.get_liquidaciones(137, top=500)
    found = next((l for l in liqs if l.id == ayc_id), None)
    if found:
        print(f"  ENCONTRADA: id={found.id}  numero={found.numero_liquidacion}  "
              f"estado={found.estado!r}  fecha={found.fecha_liquidacion}")
    else:
        print(f"  No encontrada en Top=500 de cd_id=137.")


async def set_estado_soap(
    gw: ZeepCdLiquidacionesGateway, ayc_id: int, nuevo_estado: str, usuario: str
) -> None:
    print(f"\n[SOAP] setLiquidationStatus(id={ayc_id}, newStatus={nuevo_estado!r}, usuario={usuario!r})")
    try:
        await gw.set_estado(ayc_id, nuevo_estado, usuario)
        print("  OK — sin excepción. Verificando estado resultante...")
        liqs = await gw.get_liquidaciones(137, top=500)
        found = next((l for l in liqs if l.id == ayc_id), None)
        if found:
            print(f"  Estado en AyC ahora: {found.estado!r}")
        else:
            print("  No encontrada en Top=500 para confirmar el estado.")
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")
        raise


async def void_soap(gw: ZeepCdLiquidacionesGateway, ayc_id: int) -> None:
    print(f"\n[SOAP] voidLiquidation(id={ayc_id})")
    try:
        await gw.void_liquidacion(ayc_id)
        print("  OK — sin excepción.")
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")
        raise


async def update_local_estado(numero: str, nuevo_estado: str) -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        result = await session.execute(
            text("UPDATE liquidaciones SET estado=:estado WHERE numero_liquidacion=:numero RETURNING id"),
            {"estado": nuevo_estado, "numero": numero},
        )
        rows = result.fetchall()
        await session.commit()
        if rows:
            print(f"  DB local actualizada: {rows[0][0]} → estado='{nuevo_estado}'")
        else:
            print(f"  Liquidación {numero!r} no encontrada en DB local (puede ser normal si no se sincronizó).")
    await engine.dispose()


async def delete_local(numero: str) -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        result = await session.execute(
            text("DELETE FROM liquidaciones WHERE numero_liquidacion=:numero RETURNING id"),
            {"numero": numero},
        )
        rows = result.fetchall()
        await session.commit()
        if rows:
            print(f"  DB local: eliminada {rows[0][0]}")
        else:
            print(f"  DB local: {numero!r} no existía (nada que eliminar).")
    await engine.dispose()


async def main(numero: str, accion: str, usuario: str) -> None:
    ayc_id = _parse_ayc_id(numero)
    numero_esperado = numero_liquidacion(ayc_id)
    print(f"\nLiquidación de prueba: {numero!r}  (AyC id={ayc_id}, DV correcto → {numero_esperado!r})")
    if numero != numero_esperado:
        print(f"  AVISO: el dígito verificador de {ayc_id} debería ser {numero_esperado!r}. "
              "Verificá el número — el AyC ID se deriva igual del prefijo.")

    gw = ZeepCdLiquidacionesGateway()

    if accion == "consultar":
        await consultar(gw, ayc_id)

    elif accion == "observar":
        await set_estado_soap(gw, ayc_id, "Observada", usuario)
        await update_local_estado(numero, "observada")

    elif accion == "aprobar":
        await set_estado_soap(gw, ayc_id, "Aprobada", usuario)
        await update_local_estado(numero, "aprobada")

    elif accion == "anular":
        confirm = input(f"\n¿Anular {numero!r} en wsAyC Y eliminar de DB local? [s/N] ").strip().lower()
        if confirm != "s":
            print("Cancelado.")
            return
        await void_soap(gw, ayc_id)
        await delete_local(numero)

    print("\nListo.")


parser = argparse.ArgumentParser(description="Test SOAP writes para liquidaciones (solo prueba)")
parser.add_argument("--numero", required=True, help="Número de liquidación AyC (ej: 3950-4)")
parser.add_argument(
    "--accion",
    required=True,
    choices=["consultar", "observar", "aprobar", "anular"],
)
parser.add_argument("--usuario", default="Test HelpDesk", help="Usuario para auditoría en AyC")
args = parser.parse_args()

asyncio.run(main(args.numero, args.accion, args.usuario))
