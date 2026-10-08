"""Acceso a la DB de dev de HDM desde el host, compartido por el servidor MCP
(`reportes_app_mcp.py`) y el integrador de ramas (`integrar_reportes.py`): puerto
publicado en 127.0.0.1 y credenciales del `.env` de la raíz del repo."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

RAIZ = Path(__file__).resolve().parents[2]
Conexion = psycopg.Connection[dict[str, Any]]


def _env() -> dict[str, str]:
    pares = (
        linea.split("=", 1)
        for linea in (RAIZ / ".env").read_text().splitlines()
        if "=" in linea and not linea.lstrip().startswith("#")
    )
    return {k.strip(): v.strip().strip("\"'") for k, v in pares}


def conectar() -> Conexion:
    env = _env()
    return psycopg.connect(
        host="127.0.0.1",
        port=int(env.get("DB_PORT", "5439")),
        user=env.get("POSTGRES_USER", "helpdesk"),
        password=env["POSTGRES_PASSWORD"],
        dbname=env.get("POSTGRES_DB", "helpdesk"),
        row_factory=dict_row,
    )


def avisar_superadmin(
    con: Conexion, motivo: str, id: str, titulo: str, cuerpo: str
) -> None:
    """Campanita: la audiencia `superadmin` no la tiene ningún usuario común, así
    que solo la ven los superadmin. La clave lleva la hora para que cada vuelta
    (p. ej. una nueva propuesta tras pedir cambios) vuelva a avisar."""
    con.execute(
        """INSERT INTO notificaciones (clave, audiencia, titulo, cuerpo, url)
           VALUES (%s, 'superadmin', %s, %s, '/admin/reportes')
           ON CONFLICT (clave) DO NOTHING""",
        (f"reportes-app.{motivo}:{id}:{datetime.now(UTC).isoformat()}", titulo, cuerpo),
    )
