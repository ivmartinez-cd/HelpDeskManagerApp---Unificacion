"""Comparación puntual Orion (consultas/reportes, `reportes.cdsa.com.ar:1433`, hoy
default en settings — ADR-039) vs Mercurio (productivo, con escrituras) con las
mismas credenciales SiGesReadOnly. Evidencia que sostuvo la migración de settings
de Mercurio a Orion (2026-09-11): mismo count en `dbo.Moneda` y mismo último
`Fecha_Proceso` de `dbo.Factura_Anexo` en ambos, relojes de servidor a <1s de
diferencia — sin lag visible en esa muestra puntual.

Solo SELECTs, autocommit=True, close() explícito. Script exploratorio, no forma parte
del código de producción.

Uso (dentro del contenedor backend):
    uv run python scripts/explore_orion_vs_mercurio.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings

_TIMEOUT_SECONDS = 30
_MERCURIO_HOST = "MERCURIO.cdsa.com.ar"

_SQL_IDENTIDAD = "SELECT @@SERVERNAME AS servidor, GETDATE() AS ahora"
_SQL_CONTEO_MONEDA = "SELECT COUNT(*) AS n FROM dbo.Moneda"
_SQL_ULTIMO_PROCESO = (
    "SELECT MAX(Fecha_Proceso) AS ultimo FROM dbo.Factura_Anexo"
)


def _connect(host: str, settings) -> pyodbc.Connection:
    encrypt = "yes" if settings.orion_encrypt else "no"
    conn_str = (
        f"DRIVER={settings.orion_driver};"
        f"SERVER={host};"
        f"DATABASE={settings.orion_database};"
        f"UID={settings.orion_user};"
        f"PWD={settings.orion_password.get_secret_value()};"
        f"Encrypt={encrypt};"
        "TrustServerCertificate=yes"
    )
    return pyodbc.connect(conn_str, timeout=_TIMEOUT_SECONDS, autocommit=True)


def _comparar(nombre: str, host: str, settings) -> None:
    print(f"\n=== {nombre} ({host}) ===")
    try:
        conn = _connect(host, settings)
    except pyodbc.Error as e:
        print(f"  ERROR de conexión: {e}")
        return
    try:
        conn.timeout = _TIMEOUT_SECONDS
        cur = conn.cursor()
        cur.execute(_SQL_IDENTIDAD)
        row = cur.fetchone()
        print(f"  Servidor: {row.servidor}   Hora del server: {row.ahora}")
        cur.execute(_SQL_CONTEO_MONEDA)
        print(f"  dbo.Moneda (filas): {cur.fetchone().n}")
        cur.execute(_SQL_ULTIMO_PROCESO)
        print(f"  dbo.Factura_Anexo — último Fecha_Proceso: {cur.fetchone().ultimo}")
    finally:
        conn.close()


def main() -> None:
    settings = get_settings()
    if not settings.orion_host:
        raise SystemExit("Falta ORION_HOST en .env.")
    _comparar("ORION (consultas/reportes, default)", settings.orion_host, settings)
    _comparar("MERCURIO (productivo, referencia)", _MERCURIO_HOST, settings)


if __name__ == "__main__":
    main()
