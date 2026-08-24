import uuid
from datetime import UTC, date, datetime

import pytest

from src.modules.bono_tecnicos.domain.entities.solicitud_tv import EstadoSolicitudTv, SolicitudTv
from src.modules.bono_tecnicos.domain.errors import CampoRequeridoError


def _solicitud(**overrides: object) -> SolicitudTv:
    base = {
        "id": uuid.uuid4(),
        "id_tecnico": 1314,
        "tecnico": "CD - Agustin HACZEK",
        "fecha": date(2026, 5, 18),
        "razon_social": "Exolgan",
        "sucursal": "Dock Sur",
        "tarea_realizada": "Se buscan toner en Drago y se llevan a Exolgan.",
        "estado": EstadoSolicitudTv.PENDIENTE,
        "creado_en": datetime.now(UTC),
    }
    base.update(overrides)
    return SolicitudTv(**base)  # type: ignore[arg-type]


def test_periodo_se_deriva_de_la_fecha() -> None:
    solicitud = _solicitud(fecha=date(2026, 5, 18))

    assert solicitud.periodo == 202605


@pytest.mark.parametrize("campo", ["razon_social", "sucursal", "tarea_realizada"])
def test_rechaza_campos_vacios(campo: str) -> None:
    with pytest.raises(CampoRequeridoError):
        _solicitud(**{campo: "   "})


def test_aprobar_cambia_estado_y_registra_quien_decidio() -> None:
    solicitud = _solicitud()
    ahora = datetime.now(UTC)

    solicitud.aprobar(ahora, "supervisor@canaldirecto.com.ar")

    assert solicitud.estado is EstadoSolicitudTv.APROBADA
    assert solicitud.resuelta_en == ahora
    assert solicitud.resuelta_por_email == "supervisor@canaldirecto.com.ar"
    assert solicitud.motivo_rechazo is None


def test_rechazar_cambia_estado_y_guarda_motivo() -> None:
    solicitud = _solicitud()
    ahora = datetime.now(UTC)

    solicitud.rechazar(ahora, "supervisor@canaldirecto.com.ar", "Tarea duplicada")

    assert solicitud.estado is EstadoSolicitudTv.RECHAZADA
    assert solicitud.motivo_rechazo == "Tarea duplicada"


def test_dos_solicitudes_son_iguales_solo_si_tienen_el_mismo_id() -> None:
    id_compartido = uuid.uuid4()
    a = _solicitud(id=id_compartido)
    b = _solicitud(id=id_compartido, tecnico="CD - Otro Nombre")

    assert a == b
    assert a != _solicitud()
