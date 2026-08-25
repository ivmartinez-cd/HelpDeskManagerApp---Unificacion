from datetime import date

from src.modules.bono_tecnicos.application.dtos.solicitud_tv_dto import (
    CrearSolicitudTvAdminRequest,
)
from src.modules.bono_tecnicos.application.use_cases.crear_solicitud_tv_admin import (
    CrearSolicitudTvAdmin,
)
from src.modules.bono_tecnicos.domain.entities.solicitud_tv import EstadoSolicitudTv
from tests.unit.application.bono_tecnicos.fakes import FakeSolicitudTvRepository


def _request(**overrides: object) -> CrearSolicitudTvAdminRequest:
    base = {
        "id_tecnico": 1314,
        "tecnico": "CD - Agustin HACZEK",
        "fecha": date(2026, 5, 18),
        "razon_social": "Exolgan",
        "sucursal": "Dock Sur",
        "tarea_realizada": "Se buscan toner en Drago y se llevan a Exolgan.",
        "resuelta_por_email": "supervisor@canaldirecto.com.ar",
    }
    base.update(overrides)
    return CrearSolicitudTvAdminRequest(**base)  # type: ignore[arg-type]


async def test_crea_la_solicitud_ya_aprobada() -> None:
    repo = FakeSolicitudTvRepository()
    use_case = CrearSolicitudTvAdmin(repo)

    dto = await use_case.execute(_request())

    assert dto.estado == EstadoSolicitudTv.APROBADA.value
    assert dto.periodo == 202605
    assert dto.resuelta_por_email == "supervisor@canaldirecto.com.ar"
    assert dto.resuelta_en is not None


async def test_hace_un_solo_insert_sin_pasar_por_save() -> None:
    repo = FakeSolicitudTvRepository()
    use_case = CrearSolicitudTvAdmin(repo)

    dto = await use_case.execute(_request())

    assert len(repo.add_calls) == 1
    assert repo.add_calls[0].id == dto.id
    assert repo.save_calls == []


async def test_queda_guardada_para_el_tecnico_pedido() -> None:
    repo = FakeSolicitudTvRepository()
    use_case = CrearSolicitudTvAdmin(repo)

    dto = await use_case.execute(_request(id_tecnico=2020, tecnico="CD - Otro Tecnico"))

    guardada = await repo.get_by_id(dto.id)
    assert guardada is not None
    assert guardada.id_tecnico == 2020
    assert guardada.tecnico == "CD - Otro Tecnico"
