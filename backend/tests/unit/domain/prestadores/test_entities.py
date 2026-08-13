"""Identidad de las entidades de prestadores: igualdad y hash por `id`, no por
valores — dos snapshots de la misma fila son la misma entidad."""

import uuid
from datetime import date

from src.modules.prestadores.domain.entities.asignacion_historial import AsignacionHistorial
from src.modules.prestadores.domain.entities.contacto_prestador import ContactoPrestador
from src.modules.prestadores.domain.entities.prestador import Prestador


def _prestador(prestador_id: uuid.UUID, den_comercial: str) -> Prestador:
    return Prestador(
        id=prestador_id,
        siges_empresa_id=1,
        den_comercial=den_comercial,
        razon_social=None,
        cuit=None,
        equipos=None,
        operador_id=None,
        is_active=True,
    )


def test_prestador_es_igual_por_id_aunque_cambien_los_datos() -> None:
    prestador_id = uuid.uuid4()
    assert _prestador(prestador_id, "Antes") == _prestador(prestador_id, "Después")
    assert _prestador(uuid.uuid4(), "A") != _prestador(uuid.uuid4(), "A")
    assert _prestador(prestador_id, "A") != "no soy un prestador"
    assert hash(_prestador(prestador_id, "A")) == hash(_prestador(prestador_id, "B"))


def test_contacto_es_igual_por_id() -> None:
    contacto_id = uuid.uuid4()

    def contacto(nombre: str) -> ContactoPrestador:
        return ContactoPrestador(
            id=contacto_id,
            prestador_id=uuid.uuid4(),
            nombre=nombre,
            telefono=None,
            email=None,
            is_principal=False,
            sort_order=0,
        )

    assert contacto("Juan") == contacto("Pedro")
    assert contacto("Juan") != "no soy un contacto"
    assert hash(contacto("Juan")) == hash(contacto("Pedro"))


def test_tramo_de_historial_es_igual_por_id() -> None:
    tramo_id = uuid.uuid4()

    def tramo(desde: date) -> AsignacionHistorial:
        return AsignacionHistorial(
            id=tramo_id,
            prestador_id=uuid.uuid4(),
            operador_id=None,
            desde=desde,
            hasta=None,
        )

    assert tramo(date(2026, 1, 1)) == tramo(date(2026, 2, 1))
    assert tramo(date(2026, 1, 1)) != "no soy un tramo"
    assert hash(tramo(date(2026, 1, 1))) == hash(tramo(date(2026, 2, 1)))
