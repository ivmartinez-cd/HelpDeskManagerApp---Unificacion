"""Backfill de `liquidaciones.factura_pdf_url` para filas calculadas antes del
fix del slug de `rs_prestador` (bug: un punto de abreviatura como "S.A."
se convertía en "_" igual que un espacio, ej. PENTACOM S.A. ->
`pentacom_s_a_...pdf` en vez de `pentacom_s.a....pdf` — link roto, 404 real
verificado contra la liquidación 3959-8, período 2026-08, 2026-09-07).

`_actualizar_factura` (`_reconciliar_extra_y_factura.py`) no recalcula sola
una vez que `factura_pdf_url` ya está seteada y `numero_factura` no cambió —
a propósito, porque `Fecha` de `getLiquidationById` no es estable entre
llamadas y recalcular pisaría una URL válida con una fecha distinta. Este
script evita ese problema: NO vuelve a pedir `Fecha` a AyC, reusa la fecha ya
grabada en la URL persistida (parseada del propio string) y solo pide
`RsPrestador` fresco (`get_detalle`, solo lectura) para reconstruir el slug
con la función corregida. Si el nuevo cálculo da igual a lo ya guardado, no
escribe nada.

Uso (parado en `backend/`, dentro del contenedor):
  uv run python scripts/backfill_factura_pdf_url_slug.py --periodo 2026-08 --dry-run
  uv run python scripts/backfill_factura_pdf_url_slug.py --periodo 2026-08 --check
  uv run python scripts/backfill_factura_pdf_url_slug.py --periodo 2026-08

Sin `--periodo`, recorre todo el histórico. Sin `--dry-run`/`--check`, pega
contra wsAyC real (solo lectura, `get_detalle`) y escribe en la DB real de la
instancia donde se ejecuta (DATABASE_URL del .env local).
"""

import argparse
import asyncio
import re
from datetime import datetime

from src.modules.liquidaciones.domain.services.factura_pdf_url import armar_factura_pdf_url
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_liquidacion_repository import (  # noqa: E501
    SqlAlchemyLiquidacionRepository,
)
from src.modules.liquidaciones.infrastructure.soap.zeep_cd_liquidaciones_gateway import (
    ZeepCdLiquidacionesGateway,
)
from src.shared.infrastructure.database.session import get_sessionmaker

_FECHA_EN_URL = re.compile(r"/(\d{8})_")


async def _run(periodo: str | None, dry_run: bool, check: bool) -> None:
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        liquidaciones = SqlAlchemyLiquidacionRepository(session)
        candidatas = [
            liq
            for liq in await liquidaciones.list_filtered(periodo=periodo)
            if liq.numero_factura and liq.factura_pdf_url and liq.numero_liquidacion
        ]
        etiqueta = periodo or "todos los períodos"
        print(f"Liquidaciones con factura+url ({etiqueta}): {len(candidatas)}")
        if not candidatas:
            return
        if dry_run:
            print("--dry-run: no se pega contra AyC. Candidatas:")
            for liq in candidatas:
                print(f"  numero_liquidacion={liq.numero_liquidacion} url={liq.factura_pdf_url}")
            return

        cd_gateway = ZeepCdLiquidacionesGateway()
        corregidas = 0
        sin_cambio = 0
        sin_datos = 0
        for liq in candidatas:
            assert liq.numero_liquidacion is not None
            assert liq.numero_factura is not None
            assert liq.factura_pdf_url is not None
            match_fecha = _FECHA_EN_URL.search(liq.factura_pdf_url)
            if match_fecha is None:
                print(f"  SIN FECHA PARSEABLE numero_liquidacion={liq.numero_liquidacion}")
                sin_datos += 1
                continue
            fecha = datetime.strptime(match_fecha.group(1), "%Y%m%d").date()

            ayc_id = int(liq.numero_liquidacion.split("-")[0])
            detalle = await cd_gateway.get_detalle(ayc_id)
            if detalle is None or not detalle.rs_prestador:
                print(f"  SIN rs_prestador de AyC numero_liquidacion={liq.numero_liquidacion}")
                sin_datos += 1
                continue

            nueva_url = armar_factura_pdf_url(
                fecha=fecha,
                rs_prestador=detalle.rs_prestador,
                numero_factura=liq.numero_factura,
                numero_liquidacion=liq.numero_liquidacion,
            )
            if nueva_url == liq.factura_pdf_url:
                sin_cambio += 1
                continue

            print(f"  numero_liquidacion={liq.numero_liquidacion}")
            print(f"    antes:  {liq.factura_pdf_url}")
            print(f"    ahora:  {nueva_url}")
            corregidas += 1
            if not check:
                await liquidaciones.update_numero_factura(liq.id, liq.numero_factura, nueva_url)

        if not check:
            await session.commit()
        modo = "check (sin escribir)" if check else "aplicado"
        print(f"{modo} — corregidas={corregidas} sin_cambio={sin_cambio} sin_datos={sin_datos}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--periodo", default=None, help="YYYY-MM; sin esto, todo el histórico")
    parser.add_argument("--dry-run", action="store_true", help="Solo listar candidatas")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Lee de AyC y muestra qué cambiaría, sin escribir en la DB",
    )
    args = parser.parse_args()
    asyncio.run(_run(args.periodo, args.dry_run, args.check))


if __name__ == "__main__":
    main()
