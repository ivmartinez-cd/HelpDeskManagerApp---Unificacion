"""Explora el esquema de Siges/MERCURIO buscando el dominio de "planificación de
facturación" que hoy se scrapea de Gestión (ver ADR-012 y
SIGES_READONLY_PLANIFICACION_VALIDACION.md). Antes de leer nada, verifica y muestra
qué permisos tiene realmente la cuenta conectada, para no asumir "solo lectura" solo
porque el login se llama `SiGesReadOnly`.

Rondas 1-4 (documentadas en SIGES_READONLY_PLANIFICACION_VALIDACION.md) confirmaron
`UsuariosWeb` como catálogo real de operadores. Ronda 5: el usuario dudó, con razón,
de que `Remito_Cab` sea el mismo dominio que los eventos de facturación — podría ser
entrega de insumos/partes, no lo mismo que planifica Gestión. Dato de contexto real ya
verificado en la DB local (`contadores_calendar_events`, 828 eventos sincronizados):
`bultos`/`costo_seguro`/`costo_recambio` están SIEMPRE en NULL en los eventos reales, así
que no hay valor para comparar por monto — la única verificación posible es cruzar
cliente real (tomado de un evento sincronizado) contra `dbo.Empresa`/`Remito_Cab` y ver
si hay remitos de ese cliente cerca de la fecha del evento.

Conexión efímera, `autocommit=True` (no deja transacciones abiertas) y `close()`
explícito en `finally` — no debería quedar nada colgado en el servidor más allá de la
duración de esta ejecución.

Uso (dentro del contenedor backend, con `uv`):
    uv run python scripts/explore_siges_planificacion.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 15

_SQL_IDENTIDAD = "SELECT SUSER_SNAME() AS login_name, CURRENT_USER AS db_user, DB_NAME() AS db_name"

_SQL_ROLES = """
SELECT
    IS_ROLEMEMBER('db_datareader') AS es_datareader,
    IS_ROLEMEMBER('db_datawriter') AS es_datawriter,
    IS_ROLEMEMBER('db_owner') AS es_owner,
    IS_ROLEMEMBER('db_ddladmin') AS es_ddladmin
"""

_SQL_PERMISOS_DE_ESCRITURA = """
SELECT permission_name
FROM fn_my_permissions(NULL, 'DATABASE')
WHERE permission_name IN ('INSERT', 'UPDATE', 'DELETE', 'ALTER', 'CREATE TABLE', 'CONTROL')
ORDER BY permission_name
"""

_SQL_EMPRESA_POR_NOMBRE = (
    "SELECT ID_Empresa, Den_Comercial, razon_social FROM dbo.Empresa WHERE Den_Comercial LIKE ?"
)

_SQL_REMITOS_POR_EMPRESA = """
SELECT TOP 5 Id_Remito, Remito_Nro, Fecha_Remito, Fecha_Entrega, Bultos, CostoSeguro, TipoRemito
FROM Remito_Cab
WHERE Id_Empresa = ?
ORDER BY Fecha_Remito DESC
"""

# Clientes reales de eventos "(Facturación)" ya sincronizados en contadores_calendar_events
# (event_date 2026-11-10/11), elegidos por nombre simple sin caracteres raros para el LIKE.
_CLIENTES_A_CRUZAR = ["YKK", "EDERSA", "YAGUAR"]


def _verificar_permisos(cursor: pyodbc.Cursor) -> None:
    cursor.execute(_SQL_IDENTIDAD)
    identidad = cursor.fetchone()
    print(
        f"Conectado como: {identidad.login_name} "
        f"(db_user={identidad.db_user}, db={identidad.db_name})"
    )

    cursor.execute(_SQL_ROLES)
    roles = cursor.fetchone()
    print(
        f"Roles: db_datareader={bool(roles.es_datareader)} "
        f"db_datawriter={bool(roles.es_datawriter)} "
        f"db_owner={bool(roles.es_owner)} db_ddladmin={bool(roles.es_ddladmin)}"
    )

    cursor.execute(_SQL_PERMISOS_DE_ESCRITURA)
    permisos_escritura = list(cursor.fetchall())
    if permisos_escritura:
        print("¡ATENCION! Permisos de escritura/DDL otorgados a nivel base:")
        for fila in permisos_escritura:
            print(f"  {fila.permission_name}")
    else:
        print("Sin permisos de escritura/DDL a nivel base: confirmado solo lectura.")


def _remitos_de_empresa(cursor: pyodbc.Cursor, id_empresa: int) -> list[pyodbc.Row]:
    cursor.execute(_SQL_REMITOS_POR_EMPRESA, id_empresa)
    return list(cursor.fetchall())


def _cruzar_cliente(cursor: pyodbc.Cursor, nombre: str) -> None:
    cursor.execute(_SQL_EMPRESA_POR_NOMBRE, f"%{nombre}%")
    empresas = list(cursor.fetchall())
    print(f"\n=== Cliente {nombre!r}: {len(empresas)} empresa(s) en dbo.Empresa ===")
    for empresa in empresas:
        print(f"  ID_Empresa={empresa.ID_Empresa} Den_Comercial={empresa.Den_Comercial!r}")
        remitos = _remitos_de_empresa(cursor, empresa.ID_Empresa)
        if not remitos:
            print("    Sin remitos en Remito_Cab para esta empresa.")
            continue
        for r in remitos:
            print(
                f"    Remito {r.Remito_Nro} Fecha_Remito={r.Fecha_Remito} "
                f"Fecha_Entrega={r.Fecha_Entrega} Bultos={r.Bultos} "
                f"CostoSeguro={r.CostoSeguro} TipoRemito={r.TipoRemito!r}"
            )


def main() -> None:
    settings = get_settings()
    if not settings.sla_mercurio_host:
        raise SystemExit(
            "Falta SLA_MERCURIO_HOST en .env — no hay conexión configurada a Siges/MERCURIO."
        )

    conn_str = build_mercurio_connection_string(settings)
    connection = pyodbc.connect(conn_str, timeout=_TIMEOUT_SECONDS, autocommit=True)
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()
        _verificar_permisos(cursor)
        for nombre in _CLIENTES_A_CRUZAR:
            _cruzar_cliente(cursor, nombre)
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente — nada queda abierto contra el servidor.")


if __name__ == "__main__":
    main()
