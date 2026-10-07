"""Corrige `liquidaciones.factura_pdf_url` contra el listado real de archivos de
webagentes, en vez de reconstruir el nombre (`domain/services/factura_pdf_url.py`).

Hallazgo 2026-10-07: de 770 links guardados, 605 daban 404. El nombre real no
sale de ningún dato de AyC ni de Siges (dbo.Liquidacion solo tiene
FacturaLocal/FacturaNro): la fecha del prefijo no es `Fecha` de AyC, el slug
viejo cambiaba "s.r.l." por "s_r_l", y hay tres formatos de archivo:

- `factura-2780-3.pdf` (hasta ~2023)
- `20260801_gestion_integral_s.r.l._fc-2-1575_3929-7.pdf`
- `..._fc-3-398_2991-7-2024-07-03-130720.pdf` (re-subidas con timestamp)

El directorio tiene índice público de Apache, así que se lee una vez y se busca
por número de liquidación. Si hay varios archivos, gana el último modificado
(empate: el nombre sin timestamp). Si no hay ninguno, el link queda en NULL
(3892-4). `numero_factura` no se toca, así que no dispara el aviso de factura.

Uso (contenedor backend; sin `--aplicar` solo muestra qué cambiaría):
  uv run python scripts/backfill_factura_pdf_url_listado.py
  uv run python scripts/backfill_factura_pdf_url_listado.py --aplicar
"""

import argparse
import asyncio
import re

import httpx

from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_liquidacion_repository import (  # noqa: E501
    SqlAlchemyLiquidacionRepository,
)
from src.shared.infrastructure.database.session import get_sessionmaker

_BASE_URL = "https://webagentes.canaldirecto.com.ar/files/webagentes/liquidations/"
_FILA = re.compile(r'<a href="([^"]+\.pdf)">[^<]*</a></td><td align="right">([\d-]+ [\d:]+)')
_NUMERO = re.compile(r"(?:_|^factura-)(\d+-\d)(-\d{4}-\d\d-\d\d-\d{6})?\.pdf$")


def indexar_listado(html: str) -> dict[str, str]:
    """numero_liquidacion -> nombre de archivo elegido."""
    candidatos: dict[str, tuple[str, bool, str]] = {}
    for nombre, modificado in _FILA.findall(html):
        match = _NUMERO.search(nombre)
        if match is None:
            continue
        clave = (modificado, match.group(2) is None, nombre)
        numero = match.group(1)
        if numero not in candidatos or clave > candidatos[numero]:
            candidatos[numero] = clave
    return {numero: clave[2] for numero, clave in candidatos.items()}


async def _run(aplicar: bool) -> None:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(_BASE_URL)
        resp.raise_for_status()
    archivos = indexar_listado(resp.text)
    print(f"Archivos indexados en webagentes: {len(archivos)}")
    async with get_sessionmaker()() as session:
        repo = SqlAlchemyLiquidacionRepository(session)
        cambios = 0
        for liq in await repo.list_filtered():
            if not (liq.factura_pdf_url and liq.numero_liquidacion and liq.numero_factura):
                continue
            archivo = archivos.get(liq.numero_liquidacion)
            nueva = _BASE_URL + archivo if archivo else None
            if nueva == liq.factura_pdf_url:
                continue
            cambios += 1
            print(f"{liq.numero_liquidacion} [{liq.estado}]")
            print(f"  antes: {liq.factura_pdf_url}\n  ahora: {nueva}")
            if aplicar:
                await repo.update_numero_factura(liq.id, liq.numero_factura, nueva)
        if aplicar:
            await session.commit()
    print(f"{'aplicado' if aplicar else 'sin escribir (falta --aplicar)'}: {cambios} link(s)")


def _demo() -> None:
    html = "".join(
        f'<a href="{n}">{n}</a></td><td align="right">{m}  </td>'
        for n, m in [
            ("factura-2780-3.pdf", "2023-12-01 13:22"),
            ("20260701_x_fc-2-1567_3875-7-2026-07-13-194123.pdf", "2026-07-13 15:41"),
            ("20260701_x_fc-2-1567_3875-7.pdf", "2026-07-13 15:41"),
            ("20241001_y_fc-3-488_3577-8.pdf", "2025-10-11 16:14"),
            ("20241011_y_fc-3-488_3577-8.pdf", "2025-10-11 16:15"),
        ]
    )
    assert indexar_listado(html) == {
        "2780-3": "factura-2780-3.pdf",
        "3875-7": "20260701_x_fc-2-1567_3875-7.pdf",
        "3577-8": "20241011_y_fc-3-488_3577-8.pdf",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true", help="Escribir en la DB de HDM")
    args = parser.parse_args()
    _demo()
    asyncio.run(_run(args.aplicar))


if __name__ == "__main__":
    main()
