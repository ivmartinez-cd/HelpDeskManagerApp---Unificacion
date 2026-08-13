"""Consulta read-only contra `dbo.UsuariosWeb` de Siges — misma cuenta
`db_datareader` (`SLA_MERCURIO_USER`) que ya usa `sla`/`prestadores`, sin
permisos de escritura (verificado con `IS_ROLEMEMBER`/`fn_my_permissions`,
ver ADR-012). No hay forma verificada de filtrar solo "operadores de
facturación" en `UsuariosWeb` — la tabla tiene empleados de todo tipo — así
que se resuelve por `login` puntual, no se enumera el catálogo completo.
Filtrada con placeholders pyodbc, no se interpola nada (ARCHITECTURE_GUIDE
§8)."""

USUARIOS_WEB_POR_LOGINS_SQL = """
SELECT login, nombre, apellido, color
FROM dbo.UsuariosWeb
WHERE login IN ({placeholders})
"""


def build_usuarios_web_por_logins_sql(cantidad: int) -> str:
    placeholders = ", ".join("?" for _ in range(cantidad))
    return USUARIOS_WEB_POR_LOGINS_SQL.format(placeholders=placeholders)
