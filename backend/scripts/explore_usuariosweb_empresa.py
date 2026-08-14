"""Verifica si dbo.UsuariosWebEmpresa es la asignación operador↔cliente
(candidata sin explorar del catálogo SiGesReadOnly §4). Solo lectura.

Preguntas:
1. ¿Cuántas filas/usuarios distintos tiene?
2. ¿Los usuarios con más empresas son operadores internos de Canal Directo
   (id_empresa=1, tipo interno) o usuarios-portal de clientes?
3. ¿Un operador conocido de contadores (ej. vipaez) tiene filas, y las
   empresas asignadas se parecen a su cartera de facturación?

Uso (dentro del contenedor backend):
    uv run python scripts/explore_usuariosweb_empresa.py
"""

import pyodbc

from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.mercurio.connection import build_mercurio_connection_string

_TIMEOUT_SECONDS = 30

_SQL_RESUMEN = """
SELECT COUNT(*) AS filas, COUNT(DISTINCT id_usuario) AS usuarios,
       COUNT(DISTINCT id_empresa) AS empresas
FROM dbo.UsuariosWebEmpresa
"""

_SQL_TOP_USUARIOS = """
SELECT TOP 15 U.login, U.nombre, U.apellido, U.id_empresa AS empresa_del_usuario,
       U.activo, COUNT(*) AS empresas_asignadas
FROM dbo.UsuariosWebEmpresa UE
INNER JOIN dbo.UsuariosWeb U ON U.id_usuario = UE.id_usuario
GROUP BY U.login, U.nombre, U.apellido, U.id_empresa, U.activo
ORDER BY COUNT(*) DESC
"""

_SQL_EMPRESAS_DE_UN_LOGIN = """
SELECT TOP 20 E.ID_Empresa, E.Den_Comercial, E.Estado
FROM dbo.UsuariosWebEmpresa UE
INNER JOIN dbo.UsuariosWeb U ON U.id_usuario = UE.id_usuario
INNER JOIN dbo.Empresa E ON E.ID_Empresa = UE.id_empresa
WHERE U.login = ?
ORDER BY E.Den_Comercial
"""

_SQL_CANTIDAD_DE_UN_LOGIN = """
SELECT COUNT(*) AS total
FROM dbo.UsuariosWebEmpresa UE
INNER JOIN dbo.UsuariosWeb U ON U.id_usuario = UE.id_usuario
WHERE U.login = ?
"""

_LOGINS_A_MIRAR = ["vipaez", "mpollero"]


def main() -> None:
    settings = get_settings()
    connection = pyodbc.connect(
        build_mercurio_connection_string(settings), timeout=_TIMEOUT_SECONDS, autocommit=True
    )
    try:
        connection.timeout = _TIMEOUT_SECONDS
        cursor = connection.cursor()

        cursor.execute(_SQL_RESUMEN)
        r = cursor.fetchone()
        print(
            f"UsuariosWebEmpresa: {r.filas} filas, {r.usuarios} usuarios, "
            f"{r.empresas} empresas distintas"
        )

        cursor.execute(_SQL_TOP_USUARIOS)
        print("\n=== Top usuarios por empresas asignadas ===")
        for f in cursor.fetchall():
            print(
                f"  {f.login!r} ({f.nombre} {f.apellido}, empresa={f.empresa_del_usuario}, "
                f"activo={bool(f.activo)}): {f.empresas_asignadas}"
            )

        for login in _LOGINS_A_MIRAR:
            cursor.execute(_SQL_CANTIDAD_DE_UN_LOGIN, login)
            total = cursor.fetchone().total
            print(f"\n=== {login!r}: {total} empresas asignadas ===")
            cursor.execute(_SQL_EMPRESAS_DE_UN_LOGIN, login)
            for f in cursor.fetchall():
                print(f"  {f.ID_Empresa} {f.Den_Comercial!r} (Estado={f.Estado})")
    finally:
        connection.close()
        print("\nConexión cerrada explícitamente.")


if __name__ == "__main__":
    main()
