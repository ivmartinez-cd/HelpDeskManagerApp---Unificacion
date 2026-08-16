"""Adapter pyodbc del puerto SigesCatalogoGateway. La plomería pyodbc vive en
el `MercurioQueryRunner` compartido (ADR-018); acá quedan el SQL y el mapeo de
filas propios del catálogo PST/SPST de liquidaciones."""

from typing import Any

from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCostoServicio,
    SigesEmpresaInfo,
    SigesSucursalCliente,
    SigesSucursalPropia,
    TipoEmpresaSiges,
)
from src.modules.liquidaciones.infrastructure.siges.query import (
    EMPRESAS_PST_ACTIVAS_SQL,
    SUCURSALES_DE_EMPRESA_SQL,
    SUCURSALES_DE_PRESTADOR_SQL,
    build_costos_habilitados_sql,
)
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


def _texto(value: Any) -> str | None:
    if value is None:
        return None
    texto = str(value).strip()
    return texto or None


def _tipo(den_comercial: str) -> TipoEmpresaSiges:
    return "SPST" if den_comercial.upper().startswith("SPST") else "PST"


def _numero(value: Any) -> float:
    """NULL en cualquier columna de costo/km de `CostoServicio` (pasa en datos
    reales) equivale a 0.0 — "no presta ese servicio", que el pivot ya filtra."""
    return 0.0 if value is None else float(value)


def _domicilio(value: Any) -> str | None:
    """`Sucursal.Domicilio` real viene con ruido de plantilla (' 0 Piso: Dpto:')
    cuando no está cargado — se limpia para no prefillear basura en el form."""
    texto = _texto(value)
    if texto is None:
        return None
    limpio = texto.removesuffix("Piso: Dpto:").strip()
    return limpio if limpio and limpio != "0" else None


class PyodbcSigesCatalogoGateway:
    def __init__(self, runner: MercurioQueryRunner) -> None:
        self._runner = runner

    async def list_empresas_activas(self) -> list[SigesEmpresaInfo]:
        rows = await self._runner.fetch_all(
            EMPRESAS_PST_ACTIVAS_SQL,
            gateway="siges_catalogo",
            log_message="Fallo la consulta del catálogo PST/SPST contra Siges/MERCURIO",
        )
        return [
            SigesEmpresaInfo(
                siges_empresa_id=int(row.ID_Empresa),
                den_comercial=str(row.Den_Comercial).strip(),
                razon_social=_texto(row.razon_social),
                cuit=_texto(row.cuit),
                tipo=_tipo(str(row.Den_Comercial).strip()),
            )
            for row in rows
        ]

    async def list_costos_habilitados(
        self, siges_empresa_ids: list[int]
    ) -> list[SigesCostoServicio]:
        if not siges_empresa_ids:
            return []
        rows = await self._runner.fetch_all(
            build_costos_habilitados_sql(len(siges_empresa_ids)),
            siges_empresa_ids,
            gateway="siges_catalogo",
            log_message="Fallo la consulta de CostoServicio contra Siges/MERCURIO",
            log_extra={"cantidad_ids": len(siges_empresa_ids)},
        )
        return [
            SigesCostoServicio(
                siges_empresa_id=int(row.ID_Empresa),
                descripcion=str(row.descripcion).strip(),
                vigencia_desde=row.fecha_vigencia.date(),
                costo_km=_numero(row.CostoKm),
                correctivo=_numero(row.correctivo),
                preventivo=_numero(row.preventivo),
                instalacion=_numero(row.instalacion),
                pre_correctivo=_numero(row.PreCorrectivo),
                guardia=_numero(row.guardia),
                sistemas=_numero(row.sistemas),
            )
            for row in rows
        ]

    async def list_sucursales_de_prestador(
        self, siges_empresa_id: int
    ) -> list[SigesSucursalCliente]:
        rows = await self._runner.fetch_all(
            SUCURSALES_DE_PRESTADOR_SQL,
            (siges_empresa_id,),
            gateway="siges_catalogo",
            log_message="Fallo la consulta de sucursales contra Siges/MERCURIO",
            log_extra={"siges_empresa_id": siges_empresa_id},
        )
        return [
            SigesSucursalCliente(
                siges_sucursal_id=int(row.Id_Sucursal),
                empresa_nombre=str(row.Den_Comercial).strip(),
                sucursal_nombre=str(row.descripcion).strip(),
                domicilio=_domicilio(row.Domicilio),
                localidad=_texto(row.DesCiudad),
                provincia=_texto(row.DesProvincia),
                latitud=_texto(row.Latitud),
                longitud=_texto(row.Longitud),
            )
            for row in rows
        ]

    async def list_sucursales_de_empresa(
        self, siges_empresa_id: int
    ) -> list[SigesSucursalPropia]:
        rows = await self._runner.fetch_all(
            SUCURSALES_DE_EMPRESA_SQL,
            (siges_empresa_id,),
            gateway="siges_catalogo",
            log_message="Fallo la consulta de sucursales propias contra Siges/MERCURIO",
            log_extra={"siges_empresa_id": siges_empresa_id},
        )
        return [
            SigesSucursalPropia(
                siges_sucursal_id=int(row.Id_Sucursal),
                descripcion=str(row.descripcion).strip(),
                latitud=_texto(row.Latitud),
                longitud=_texto(row.Longitud),
            )
            for row in rows
        ]
