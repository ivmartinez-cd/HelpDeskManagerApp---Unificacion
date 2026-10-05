"""Adapter pyodbc del puerto BitacoraGateway: comentarios de PST en la
bitácora de liquidaciones de Web Agentes (`dbo.Bitacora`). Solo lectura.

Interno vs. PST: los operadores de Canal también responden en el mismo hilo
(Origen='webagentes'); se distinguen porque su usuario de `UsuariosWeb`
pertenece a la empresa 1 (Canal Directo). Usuario sin fila en `UsuariosWeb`
('Anonimo') cuenta como PST. `OUTER APPLY TOP 1` porque `login` no es
único garantizado y un duplicado no debe repetir el comentario."""

from typing import Any

from src.modules.liquidaciones.domain.repositories.bitacora_gateway import (
    ComentarioBitacora,
    EntradaBitacora,
)
from src.shared.infrastructure.orion.query_runner import OrionQueryRunner

_EMPRESA_CANAL_DIRECTO = 1

COMENTARIOS_PST_SQL = f"""
SELECT B.ID_Consulta, B.ID_Referencia, B.Fecha, B.Usuario,
       CAST(B.Consulta AS nvarchar(max)) AS Consulta, E.Den_Comercial
FROM dbo.Bitacora B
OUTER APPLY (SELECT TOP 1 U.id_empresa FROM dbo.UsuariosWeb U
             WHERE U.login = B.Usuario) UW
LEFT JOIN dbo.Empresa E ON E.ID_Empresa = UW.id_empresa
WHERE B.Tipo = 'Liquidation' AND B.Origen = 'webagentes'
  AND B.Fecha >= DATEADD(hour, -?, GETDATE())
  AND (UW.id_empresa IS NULL OR UW.id_empresa <> {_EMPRESA_CANAL_DIRECTO})
ORDER BY B.ID_Consulta
"""

HILO_LIQUIDACION_SQL = """
SELECT B.ID_Consulta, B.Fecha, B.Usuario, CAST(B.Consulta AS nvarchar(max)) AS Consulta,
       UW.id_empresa, UW.nombre, UW.apellido, E.Den_Comercial
FROM dbo.Bitacora B
OUTER APPLY (SELECT TOP 1 U.id_empresa, U.nombre, U.apellido FROM dbo.UsuariosWeb U
             WHERE U.login = B.Usuario) UW
LEFT JOIN dbo.Empresa E ON E.ID_Empresa = UW.id_empresa
WHERE B.Tipo = 'Liquidation' AND B.Origen = 'webagentes' AND B.ID_Referencia = ?
ORDER BY B.ID_Consulta
"""


class PyodbcBitacoraGateway:
    def __init__(self, runner: OrionQueryRunner) -> None:
        self._runner = runner

    async def comentarios_pst_recientes(self, horas: int) -> list[ComentarioBitacora]:
        rows = await self._runner.fetch_all(
            COMENTARIOS_PST_SQL,
            (horas,),
            gateway="liquidaciones_bitacora",
            log_message="Fallo la lectura de la bitácora de liquidaciones en Siges/ORION",
        )
        return [
            ComentarioBitacora(
                id_consulta=int(r.ID_Consulta),
                numero_liquidacion_cd=int(r.ID_Referencia),
                fecha=r.Fecha,
                usuario=str(r.Usuario or "").strip() or "Anonimo",
                prestador=(str(r.Den_Comercial).strip() or None) if r.Den_Comercial else None,
                texto=str(r.Consulta or "").strip(),
            )
            for r in rows
        ]

    async def hilo_de_liquidacion(self, numero_liquidacion_cd: int) -> list[EntradaBitacora]:
        rows = await self._runner.fetch_all(
            HILO_LIQUIDACION_SQL,
            (numero_liquidacion_cd,),
            gateway="liquidaciones_bitacora",
            log_message="Fallo la lectura de la bitácora de una liquidación en Siges/ORION",
        )
        return [_a_entrada(r) for r in rows]


def _a_entrada(r: Any) -> EntradaBitacora:
    es_canal = r.id_empresa == _EMPRESA_CANAL_DIRECTO
    nombre = " ".join(str(x).strip() for x in (r.nombre, r.apellido) if x and str(x).strip())
    autor = nombre if es_canal else str(r.Den_Comercial or "").strip()
    return EntradaBitacora(
        id_consulta=int(r.ID_Consulta),
        fecha=r.Fecha,
        usuario=str(r.Usuario or "").strip() or "Anonimo",
        autor=autor or None,
        es_canal=es_canal,
        texto=str(r.Consulta or "").strip(),
    )
