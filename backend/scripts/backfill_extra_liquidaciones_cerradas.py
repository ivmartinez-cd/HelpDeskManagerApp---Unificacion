"""Backfill de extra/factura para liquidaciones CERRADAS de un año dado.

Motivo: abrir el detalle de una liquidación cerrada ya dispara
`ReconciliarLiquidacionIndividual` y trae extra/factura actualizados desde AyC
(commit d86d762, 2026-08-21) — pero el sync masivo (botón "Sincronizar CD" y el
job de 120 min) excluye a propósito el estado `cerrada`
(`_ESTADOS_RECONCILIABLES` en `sincronizar_liquidaciones.py`). Este script cubre
el lote que ese sync nunca toca, sin necesidad de leer Siges/DB legacy: wsAyC sí
expone `Extra`/`DetalleExtra` para liquidaciones cerradas (verificado con la
liquidación real 3929-7, ver docs/liquidaciones/LIQUIDACION_PRESTADORES_MIGRACION_ESTADO.md).

Uso (`--anio` default es el año actual):
  uv run python scripts/backfill_extra_liquidaciones_cerradas.py --dry-run   # solo lista
  uv run python scripts/backfill_extra_liquidaciones_cerradas.py --check     # cuenta impacto
  uv run python scripts/backfill_extra_liquidaciones_cerradas.py            # pega a AyC y persiste

Script operativo, fuera de las capas domain/application/infrastructure: pega contra
wsAyC real (no hay dryRun de por medio en el gateway; --check evita la escritura en DB
pero igual hace las lecturas reales) y, sin --dry-run/--check, escribe en la DB real de
la instancia donde se ejecuta (DATABASE_URL del .env local) — confirmar el entorno antes
de correrlo (ver CLAUDE.md, "Modo test obligatorio").
"""

import argparse
import asyncio
from datetime import UTC, datetime

from src.modules.liquidaciones.domain.entities.liquidacion import ESTADO_CERRADA
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_liquidacion_repository import (  # noqa: E501
    SqlAlchemyLiquidacionRepository,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_prestador_repository import (  # noqa: E501
    SqlAlchemyPrestadorRepository,
)
from src.modules.liquidaciones.infrastructure.soap.zeep_cd_liquidaciones_gateway import (
    ZeepCdLiquidacionesGateway,
)
from src.modules.liquidaciones.presentation.dependencies import (
    build_reconciliar_liquidacion_individual,
)
from src.shared.infrastructure.database.session import get_sessionmaker


async def _check(anio: int, cerradas: list, session) -> None:
    """Mismas lecturas reales contra AyC que haría el backfill, sin persistir nada."""
    prestadores = SqlAlchemyPrestadorRepository(session)
    cd_gateway = ZeepCdLiquidacionesGateway()
    cd_liqs_por_prestador: dict = {}
    con_extra_pendiente = 0
    con_factura_pendiente = 0
    sin_vinculo_ayc = 0
    for liq in cerradas:
        prestador = await prestadores.get_by_id(liq.prestador_id)
        if prestador is None or prestador.cd_prestador_id is None or not liq.numero_liquidacion:
            sin_vinculo_ayc += 1
            continue
        if prestador.cd_prestador_id not in cd_liqs_por_prestador:
            cd_liqs_por_prestador[prestador.cd_prestador_id] = await cd_gateway.get_liquidaciones(
                prestador.cd_prestador_id
            )
        cd_liq = next(
            (
                c
                for c in cd_liqs_por_prestador[prestador.cd_prestador_id]
                if c.numero_liquidacion == liq.numero_liquidacion
            ),
            None,
        )
        if cd_liq is None:
            sin_vinculo_ayc += 1
            continue
        detalle = await cd_gateway.get_detalle(cd_liq.id)
        if detalle is None:
            continue
        if detalle.monto_extra is not None and (
            detalle.concepto_extra != liq.concepto_extra or detalle.monto_extra != liq.monto_extra
        ):
            con_extra_pendiente += 1
            print(
                f"  extra distinto numero_liquidacion={liq.numero_liquidacion} "
                f"local=({liq.concepto_extra!r}, {liq.monto_extra}) "
                f"ayc=({detalle.concepto_extra!r}, {detalle.monto_extra})"
            )
        if detalle.numero_factura is not None and detalle.numero_factura != liq.numero_factura:
            con_factura_pendiente += 1
    print(
        f"--check {anio}: extras_pendientes={con_extra_pendiente} "
        f"facturas_pendientes={con_factura_pendiente} sin_vinculo_ayc={sin_vinculo_ayc} "
        f"(sobre {len(cerradas)} cerradas)"
    )


async def _run(anio: int, dry_run: bool, check: bool) -> None:
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        liquidaciones: LiquidacionRepository = SqlAlchemyLiquidacionRepository(session)
        cerradas = await liquidaciones.list_filtered(estado=ESTADO_CERRADA, anio=anio)
        print(f"Liquidaciones cerradas {anio}: {len(cerradas)}")
        if not cerradas:
            return
        if dry_run:
            print("--dry-run: no se pega contra AyC. Ejemplo de candidatas (hasta 20):")
            for liq in cerradas[:20]:
                print(f"  numero_liquidacion={liq.numero_liquidacion} periodo={liq.periodo}")
            return
        if check:
            await _check(anio, cerradas, session)
            return

        reconciliar = build_reconciliar_liquidacion_individual(session)
        extras_actualizados = 0
        facturas_actualizadas = 0
        fallidas = 0
        for liq in cerradas:
            try:
                resultado = await reconciliar.execute(liq.id)
            except Exception as exc:  # best-effort: seguir con el resto del lote
                fallidas += 1
                print(f"  FALLO numero_liquidacion={liq.numero_liquidacion}: {exc!r}")
                continue
            if resultado.extra_actualizado:
                extras_actualizados += 1
            if resultado.factura_actualizada:
                facturas_actualizadas += 1
        await session.commit()
        print(
            f"OK — extras_actualizados={extras_actualizados} "
            f"facturas_actualizadas={facturas_actualizadas} fallidas={fallidas}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--anio", type=int, default=datetime.now(UTC).year, help="Año de periodo a backfillear"
    )
    parser.add_argument("--dry-run", action="store_true", help="Solo listar candidatas")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Lee de AyC y cuenta impacto real, sin escribir en la DB",
    )
    args = parser.parse_args()
    asyncio.run(_run(args.anio, args.dry_run, args.check))


if __name__ == "__main__":
    main()
