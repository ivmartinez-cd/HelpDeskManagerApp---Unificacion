"""Fetchea la página de edición de un evento de planificación en Gestión
para ver qué campos/IDs expone el formulario (id_empresa, id_operador,
id_cliente, etc.) — eso revela qué claves usa la app Symfony internamente
y si hay algún ID que aparezca también en SigesReadOnly.

Solo un GET de lectura con la sesión autenticada existente.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_gestion_evento_editar.py [evento_id]

Ejemplo:
    uv run python scripts/explore_gestion_evento_editar.py 921
"""

import asyncio
import re
import sys
from html.parser import HTMLParser

from src.modules.contadores.infrastructure.gestion.gestion_planificacion_client import (
    GestionPlanificacionClient,
)


class FormFieldExtractor(HTMLParser):
    """Extrae campos de formulario HTML (<input>, <select>, <textarea>)."""

    def __init__(self) -> None:
        super().__init__()
        self.fields: list[dict[str, str]] = []
        self.selects: list[dict[str, str]] = []
        self._current_select: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "input":
            self.fields.append({
                "tag": "input",
                "type": a.get("type", "text"),
                "name": a.get("name", ""),
                "value": a.get("value", ""),
                "id": a.get("id", ""),
            })
        elif tag == "select":
            self._current_select = {
                "tag": "select",
                "name": a.get("name", ""),
                "id": a.get("id", ""),
            }
        elif tag == "textarea":
            self.fields.append({
                "tag": "textarea",
                "name": a.get("name", ""),
                "id": a.get("id", ""),
                "value": "",
            })

    def handle_endtag(self, tag: str) -> None:
        if tag == "select" and self._current_select:
            self.selects.append(self._current_select)
            self._current_select = None


async def main() -> None:
    evento_id = sys.argv[1] if len(sys.argv) > 1 else "921"
    path = f"/planificacion/evento/{evento_id}/editar"

    client = GestionPlanificacionClient()
    print(f"GET {path}")
    response = await client._get(path)  # noqa: SLF001

    print(f"HTTP {response.status_code} — {len(response.text)} chars")
    html = response.text

    # Extraer campos del formulario
    parser = FormFieldExtractor()
    parser.feed(html)

    print(f"\n=== Inputs ({len(parser.fields)}) ===")
    for f in parser.fields:
        print(f"  [{f.get('type', 'text')}] name={f['name']!r}  id={f['id']!r}  value={f.get('value', '')!r}")

    print(f"\n=== Selects ({len(parser.selects)}) ===")
    for s in parser.selects:
        print(f"  name={s['name']!r}  id={s['id']!r}")

    # Buscar IDs numéricos en el HTML (patrones tipo /entidad/123 o id: 123)
    print("\n=== IDs numéricos en el HTML (rutas tipo /entidad/N) ===")
    rutas = re.findall(r'["\'/](\w+)/(\d+)["\'/]', html)
    rutas_unicas = sorted({(e, n) for e, n in rutas if e not in ("js", "css", "img", "fonts")})
    for entidad, num in rutas_unicas[:40]:
        print(f"  /{entidad}/{num}")

    # Mostrar texto visible cerca de "operador", "cliente", "empresa"
    print("\n=== Fragmentos con 'operador'/'cliente'/'empresa' (contexto 120 chars) ===")
    for patron in (r"operador", r"cliente", r"empresa", r"id_"):
        for m in re.finditer(patron, html, re.IGNORECASE):
            start = max(0, m.start() - 60)
            end = min(len(html), m.end() + 60)
            fragmento = html[start:end].replace("\n", " ").strip()
            print(f"  [{patron}] ...{fragmento}...")


if __name__ == "__main__":
    asyncio.run(main())
