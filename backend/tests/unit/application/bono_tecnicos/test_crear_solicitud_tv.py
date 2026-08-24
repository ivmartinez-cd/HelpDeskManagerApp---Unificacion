from datetime import date

import pytest

from src.modules.bono_tecnicos.application.dtos.solicitud_tv_dto import CrearSolicitudTvRequest
from src.modules.bono_tecnicos.application.use_cases.crear_solicitud_tv import CrearSolicitudTv
from src.modules.bono_tecnicos.domain.entities.solicitud_tv import EstadoSolicitudTv
from src.modules.bono_tecnicos.domain.errors import CampoRequeridoError
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo
from tests.unit.application.bono_tecnicos.fakes import FakeSolicitudTvRepository


def _request(**overrides: object) -> CrearSolicitudTvRequest:
    base = {
        "id_tecnico": 1314,
        "tecnico": "CD - Agustin HACZEK",
        "fecha": date(2026, 5, 18),
        "razon_social": "Exolgan",
        "sucursal": "Dock Sur",
        "tarea_realizada": "Se buscan toner en Drago y se llevan a Exolgan.",
    }
    base.update(overrides)
    return CrearSolicitudTvRequest(**base)  # type: ignore[arg-type]


async def test_crea_la_solicitud_pendiente() -> None:
    repo = FakeSolicitudTvRepository()
    use_case = CrearSolicitudTv(repo)

    dto = await use_case.execute(_request())

    assert dto.estado == EstadoSolicitudTv.PENDIENTE.value
    assert dto.periodo == 202605
    guardada = await repo.get_by_id(dto.id)
    assert guardada is not None
    assert guardada.id_tecnico == 1314


async def test_campo_vacio_no_guarda_nada() -> None:
    repo = FakeSolicitudTvRepository()
    use_case = CrearSolicitudTv(repo)

    with pytest.raises(CampoRequeridoError):
        await use_case.execute(_request(tarea_realizada="  "))

    assert await repo.list_by_periodo(Periodo(202605)) == []
