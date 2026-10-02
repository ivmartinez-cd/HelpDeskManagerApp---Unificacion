"""Panel de candidatos real: cada lectura sale con lo que el legacy muestra y
usa (`CandidatoContador`): etiqueta de validación, si sirve como P/L
(`EsUsableComoCandidate`), `Para_Facturar` del tipo de toma, marcas de
cambio de ubicación e `id_contador` para restaurar una P/L."""

from datetime import date
from typing import Any

import pytest

from src.modules.contadores.application.dtos.candidatos_equipo_dto import CandidatosEquipoDto
from src.modules.contadores.application.dtos.receso_dto import RecesoDto
from src.modules.contadores.application.dtos.solicitud_recalculo_siges_dto import (
    SolicitudRecalculoSigesDto,
)
from src.modules.contadores.application.use_cases.get_candidatos_equipo_siges import (
    GetCandidatosEquipoSigesUseCase,
)
from src.modules.contadores.domain.ports.candidatos_equipo_port import (
    LecturaCandidataSiges,
    MetadataEquipoSiges,
)
from tests.unit.application.contadores._fila_grilla_siges_builder import fila_siges

_METADATA = MetadataEquipoSiges("SER1", "Empresa", "Sucursal", None, "Modelo X", 1, 45.0)


class FakePort:
    def __init__(
        self,
        lecturas: list[LecturaCandidataSiges],
        metadata: MetadataEquipoSiges | None = _METADATA,
    ) -> None:
        self.lecturas = lecturas
        self.metadata = metadata

    async def fetch_lecturas(
        self, id_maquina: int, id_clase_contador: int
    ) -> list[LecturaCandidataSiges]:
        return self.lecturas

    async def fetch_lecturas_de_equipos(
        self, equipos: list[tuple[int, int]]
    ) -> dict[tuple[int, int], list[LecturaCandidataSiges]]:
        return {e: await self.fetch_lecturas(*e) for e in equipos}

    async def fetch_metadata_equipo(self, id_maquina: int) -> MetadataEquipoSiges | None:
        return self.metadata


def _lectura(tipo: int, para_facturar: bool = True, **marcas: bool) -> LecturaCandidataSiges:
    return LecturaCandidataSiges(
        id_contador=900 + tipo, fecha=date(2026, 4, 20), tipo_toma=tipo, valor=1_000.0,
        para_facturar=para_facturar, desc_tipo_toma=f"Tipo {tipo}", **marcas,
    )


async def _dto(
    *lecturas: LecturaCandidataSiges, id_tecnologia: int = 1
) -> CandidatosEquipoDto | None:
    metadata = MetadataEquipoSiges(
        "SER1", "Empresa", "Sucursal", None, "Modelo X", id_tecnologia, 45.0
    )
    return await GetCandidatosEquipoSigesUseCase(FakePort(list(lecturas), metadata)).execute(77, 10)


@pytest.mark.parametrize(
    ("tipo", "para_facturar", "etiqueta", "usable"),
    [
        (1, True, "✓ ok", True),  # real
        (8, True, "✓ ok", True),  # contador inicial
        (13, True, "✓ ok", True),  # contador final
        (16, True, "✓ ok", True),  # contador reinicial
        (4, True, "⚠ T4", True),
        (4, False, "⚠ T4-PF0", True),
        (18, True, "⚠ WC", True),  # web cliente
        (14, True, "⚠ est.", False),
        (19, True, "⚠ est.", False),
        (5, True, "—", False),  # otro tipo no reconocido
    ],
)
async def test_etiqueta_y_usabilidad_como_el_legacy(
    tipo: int, para_facturar: bool, etiqueta: str, usable: bool
) -> None:
    dto = await _dto(_lectura(tipo, para_facturar))

    assert dto is not None
    lectura = dto.lecturas[0]
    assert lectura.etiqueta_validacion == etiqueta
    assert lectura.usable is usable
    assert lectura.valido is (etiqueta == "✓ ok")
    assert lectura.motivo_invalidez == (None if etiqueta == "✓ ok" else etiqueta)
    assert lectura.para_facturar is para_facturar


async def test_propaga_id_contador_descripcion_y_marcas_de_cambio() -> None:
    dto = await _dto(_lectura(1, cambio_sucursal_vs_anterior=True))

    assert dto is not None
    lectura = dto.lecturas[0]
    assert (lectura.id_contador, lectura.desc_tipo_toma) == (901, "Tipo 1")
    assert lectura.cambio_sucursal_vs_anterior is True
    assert not (lectura.cambio_empresa_vs_anterior or lectura.cambio_anexo_vs_anterior)


@pytest.mark.parametrize(("id_tecnologia", "tecnologia"), [(1, "MONO"), (2, "COLOR"), (3, "COLOR")])
async def test_tecnologia_del_equipo(id_tecnologia: int, tecnologia: str) -> None:
    dto = await _dto(id_tecnologia=id_tecnologia)

    assert dto is not None
    assert dto.tecnologia == tecnologia


async def test_equipo_inexistente_devuelve_none() -> None:
    use_case = GetCandidatosEquipoSigesUseCase(FakePort([], metadata=None))

    assert await use_case.execute(77, 10) is None


class _FakeGrilla:
    def __init__(self, filas: list[Any]) -> None:
        self.filas = filas

    async def fetch_grilla(
        self,
        nro_proceso: int,
        fecha_objetivo: date,
        *,
        fresca: bool = False,
        operador: str | None = None,
    ) -> list[Any]:
        return self.filas


class _FakeRecesos:
    async def listar(self, id_grupo_economico: int) -> list[RecesoDto]:
        return []

    async def listar_para_proceso(self, id_anexo: int, ids_grupo: list[int]) -> list[RecesoDto]:
        return []

    async def crear(self, receso_sin_id: RecesoDto) -> RecesoDto:
        return receso_sin_id

    async def actualizar(self, receso: RecesoDto) -> RecesoDto | None:
        return receso

    async def eliminar(self, id_receso: int) -> None:
        return None


_SOLICITUD = SolicitudRecalculoSigesDto(
    nro_proceso=1, id_grupo_economico=900, id_anexo=44, fecha_objetivo=date(2026, 4, 30)
)


def _con_grilla(filas: list[Any]) -> GetCandidatosEquipoSigesUseCase:
    return GetCandidatosEquipoSigesUseCase(
        FakePort([_lectura(1)]), _FakeGrilla(filas), _FakeRecesos()
    )


async def test_cabecera_sale_del_snapshot_del_proceso_como_equipo_raw() -> None:
    # `PanelCandidatos.razor` muestra `Equipo.Raw`: empresa/sucursal/sector
    # del SNAPSHOT del proceso (lo que se factura), no la ubicación actual.
    fila = fila_siges(
        id_maquina=77, nro_serie="SNAP1", empresa_desc="Empresa al cierre",
        sucursal_desc="Suc al cierre", sector_desc="Sector 3", modelo_desc="Modelo Y",
        id_tecnologia=2, velocidad=30.0,
    )

    dto = await _con_grilla([fila]).execute(77, 10, _SOLICITUD)

    assert dto is not None
    assert (dto.nro_serie, dto.empresa, dto.sucursal, dto.sector) == (
        "SNAP1", "Empresa al cierre", "Suc al cierre", "Sector 3",
    )
    assert (dto.modelo, dto.tecnologia, dto.velocidad_ppm) == ("Modelo Y", "COLOR", 30.0)


async def test_equipo_fuera_de_la_grilla_usa_la_ubicacion_actual() -> None:
    dto = await _con_grilla([fila_siges(id_maquina=999)]).execute(77, 10, _SOLICITUD)

    assert dto is not None
    assert (dto.nro_serie, dto.empresa) == ("SER1", "Empresa")
    assert dto.boxplot is None
