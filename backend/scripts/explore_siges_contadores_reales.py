"""Explora SiGesReadOnly para reproducir la lógica del reporte legacy
`Operaciones/EquiposSinContadorReal/RUN.php`. Solo SELECTs parametrizados,
misma cuenta de solo lectura y mismo patrón que explore_siges_parque_pst.py.

Rondas 1-3 (hechas): "real" = ID_TipoToma NOT IN (8,13,14,19); FechaUltCDOR =
COALESCE(última real, primera toma histórica) — fechas exactas contra legacy;
IM-n = diffs de tomas mensuales; Propiedad = Maquina.ID_Propietario→Empresa.
Pendiente: el universo — estados {1,3,8,200,254} da 435 equipos >=100 meses
vs 30 del legacy. Hipótesis: solo equipos que siguen facturando (con tomas
recientes de cualquier tipo).

Ronda 4: paridad de conteos con filtro "tiene toma en los últimos N meses",
y origen de Observaciones (Maquina.Observ / Maquina.aviso).

Uso (dentro del contenedor backend):
    uv run python scripts/explore_siges_contadores_reales.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 300

_FECHA_ULT_REAL = """
COALESCE(
  (SELECT MAX(C.FechaTomaContador) FROM dbo.Contadores C
   WHERE C.ID_Maquina = M.ID_Maquina AND C.Estado = 0
     AND C.ID_TipoToma NOT IN (8, 13, 14, 19)),
  (SELECT MIN(C.FechaTomaContador) FROM dbo.Contadores C
   WHERE C.ID_Maquina = M.ID_Maquina AND C.Estado = 0)
)
"""

_ULTIMA_TOMA = """
(SELECT MAX(C.FechaTomaContador) FROM dbo.Contadores C
 WHERE C.ID_Maquina = M.ID_Maquina AND C.Estado = 0)
"""

_SQL_CONTEO = f"""
SELECT COUNT(*) AS equipos
FROM dbo.Maquina M
WHERE M.Estado = 0
  AND M.ID_Estado_Maquina IN (1, 3, 8, 200, 254)
  AND DATEDIFF(month, {_FECHA_ULT_REAL}, GETDATE()) >= ?
  AND DATEDIFF(month, {_ULTIMA_TOMA}, GETDATE()) <= ?
"""

_SQL_TOP = f"""
SELECT TOP 6 M.Nro_Serie,
       {_FECHA_ULT_REAL} AS fecha_ult,
       DATEDIFF(month, {_FECHA_ULT_REAL}, GETDATE()) AS meses
FROM dbo.Maquina M
WHERE M.Estado = 0
  AND M.ID_Estado_Maquina IN (1, 3, 8, 200, 254)
  AND DATEDIFF(month, {_ULTIMA_TOMA}, GETDATE()) <= ?
ORDER BY meses DESC
"""

_SQL_OBSERV_MAQUINA = """
SELECT M.Nro_Serie, M.Observ, M.aviso
FROM dbo.Maquina M
WHERE M.Nro_Serie IN (?, ?)
"""


def main() -> None:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise SystemExit("Falta SLA_MERCURIO_HOST en .env.")

    conn_str = build_mercurio_connection_string(settings)
    connection = pyodbc.connect(conn_str, timeout=_TIMEOUT_SECONDS, autocommit=True)
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()

        print("=== Conteos con filtro 'última toma <= N meses' ===")
        print("    (legacy TOP500: >=100→30, >=60→157, >=40→313, >=23→500)")
        for ultima_toma_max in (1, 2, 3):
            for umbral in (100, 60, 40, 23):
                cursor.execute(_SQL_CONTEO, umbral, ultima_toma_max)
                n = cursor.fetchone().equipos
                print(f"  ultima_toma<={ultima_toma_max}m, sin_real>={umbral}m: {n}")
            print()

        cursor.execute(_SQL_TOP, 2)
        print("=== TOP 6 (legacy: PBSSF46D 175, PBSS0027 170, Z75NBJAD 138) ===")
        for f in cursor.fetchall():
            print(f"  {f.Nro_Serie}: {f.fecha_ult:%Y-%m-%d} ({f.meses} meses)")

        cursor.execute(_SQL_OBSERV_MAQUINA, "BRBSS1B03F", "0C52BJFK10000HD")
        print("\n=== Maquina.Observ / aviso ===")
        for f in cursor.fetchall():
            print(f"  {f.Nro_Serie}: Observ={f.Observ!r} aviso={f.aviso!r}")
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
