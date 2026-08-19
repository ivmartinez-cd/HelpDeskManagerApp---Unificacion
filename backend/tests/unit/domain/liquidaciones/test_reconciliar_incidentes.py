"""reconciliar_incidentes: altas/cambios/bajas contra lo que reporta AyC, matching
por la parte numérica de `numero_incidente` (CSV trae dígito verificador, SOAP no),
tolerancia de float y `None`≡`""`, y ambigüedad ante duplicados."""

import uuid
from datetime import date

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.services.reconciliar_incidentes import (
    reconciliar_incidentes,
)
from src.modules.liquidaciones.domain.value_objects.incidente_importado import (
    IncidenteImportado,
)

_FECHA = date(2026, 7, 30)


def _local(
    numero_incidente: str = "838937",
    *,
    empresa_nombre: str | None = "Empresa Test",
    costo_servicio_cobrado: float = 1000.0,
    cant_km_cobrado: float = 0.0,
    costo_km_cobrado: float = 0.0,
) -> Incidente:
    return Incidente(
        id=uuid.uuid4(),
        liquidacion_id=uuid.uuid4(),
        numero_incidente=numero_incidente,
        rubro="Impresoras",
        tipo="correctivo",
        empresa_nombre=empresa_nombre,
        sucursal_nombre="Sucursal Test",
        nro_serie="SN-1",
        fecha_cierre=_FECHA,
        costo_servicio_cobrado=costo_servicio_cobrado,
        cant_km_cobrado=cant_km_cobrado,
        costo_km_cobrado=costo_km_cobrado,
        total_viaje_cobrado=cant_km_cobrado * costo_km_cobrado,
        costo_total_cobrado=costo_servicio_cobrado + cant_km_cobrado * costo_km_cobrado,
        pasa_it=True,
        costo_servicio_esperado=None,
        cant_km_esperado=None,
        costo_km_esperado=None,
        estado_validacion="pendiente",
    )


def _remoto(
    numero_incidente: str = "838937",
    *,
    empresa_nombre: str = "Empresa Test",
    costo_servicio_cobrado: float = 1000.0,
    cant_km_cobrado: float = 0.0,
    costo_km_cobrado: float = 0.0,
    fecha_cierre: date | None = _FECHA,
) -> IncidenteImportado:
    total_viaje = cant_km_cobrado * costo_km_cobrado
    return IncidenteImportado(
        numero_incidente=numero_incidente,
        rubro="Impresoras",
        tipo="correctivo",
        empresa_nombre=empresa_nombre,
        sucursal_nombre="Sucursal Test",
        nro_serie="SN-1",
        fecha_cierre=fecha_cierre,
        costo_servicio_cobrado=costo_servicio_cobrado,
        cant_km_cobrado=cant_km_cobrado,
        costo_km_cobrado=costo_km_cobrado,
        total_viaje_cobrado=total_viaje,
        costo_total_cobrado=costo_servicio_cobrado + total_viaje,
        pasa_it=True,
    )


def test_incidente_solo_remoto_es_alta() -> None:
    diff = reconciliar_incidentes([], [_remoto()])
    assert diff.altas == [_remoto()]
    assert diff.cambios == []
    assert diff.bajas == []
    assert diff.ambiguos == 0


def test_incidente_solo_local_es_baja() -> None:
    local = _local()
    diff = reconciliar_incidentes([local], [])
    assert diff.bajas == [local.id]
    assert diff.altas == []
    assert diff.cambios == []


def test_cambio_economico_se_detecta() -> None:
    local = _local(costo_servicio_cobrado=1000.0)
    remoto = _remoto(costo_servicio_cobrado=1500.0)
    diff = reconciliar_incidentes([local], [remoto])
    assert diff.altas == []
    assert diff.bajas == []
    [cambio] = diff.cambios
    assert cambio.incidente_id == local.id
    assert cambio.costo_servicio_cobrado == 1500.0


def test_cambio_no_economico_se_detecta() -> None:
    local = _local(empresa_nombre="Empresa Vieja")
    remoto = _remoto(empresa_nombre="Empresa Nueva")
    diff = reconciliar_incidentes([local], [remoto])
    [cambio] = diff.cambios
    assert cambio.empresa_nombre == "Empresa Nueva"


def test_sin_cambios_no_genera_nada() -> None:
    local = _local()
    remoto = _remoto()
    diff = reconciliar_incidentes([local], [remoto])
    assert diff == reconciliar_incidentes([local], [remoto])
    assert diff.altas == diff.bajas == diff.cambios == []


def test_ruido_de_redondeo_en_float_no_es_cambio() -> None:
    """Las columnas son Float y total/costo_total se recalculan con round(...) —
    un `==` estricto marcaría "cambio" en corridas idénticas."""
    local = _local(costo_servicio_cobrado=1000.0)
    remoto = _remoto(costo_servicio_cobrado=1000.004)
    diff = reconciliar_incidentes([local], [remoto])
    assert diff.cambios == []


def test_none_local_equivale_a_string_vacio_remoto() -> None:
    """`Incidente.empresa_nombre` es `str | None`; `IncidenteImportado.empresa_nombre`
    es `str` no-opcional — sin este tratamiento, todo incidente con campos vacíos
    importados por CSV se marcaría como "cambio" en cada corrida."""
    local = _local(empresa_nombre=None)
    remoto = _remoto(empresa_nombre="")
    diff = reconciliar_incidentes([local], [remoto])
    assert diff.cambios == []


def test_numero_incidente_con_digito_verificador_matchea_por_parte_numerica() -> None:
    """Liquidaciones cargadas por CSV traen dv (`"838937-1"`); el sync SOAP trae el
    id crudo (`"838937"`) — tienen que matchear como el mismo incidente."""
    local = _local(numero_incidente="838937-1")
    remoto = _remoto(numero_incidente="838937", costo_servicio_cobrado=2000.0)
    diff = reconciliar_incidentes([local], [remoto])
    assert diff.altas == []
    assert diff.bajas == []
    [cambio] = diff.cambios
    assert cambio.incidente_id == local.id


def test_numero_incidente_duplicado_local_es_ambiguo() -> None:
    local1 = _local(numero_incidente="838937-1")
    local2 = _local(numero_incidente="838937-9")
    remoto = _remoto(numero_incidente="838937")
    diff = reconciliar_incidentes([local1, local2], [remoto])
    assert diff.ambiguos == 1
    assert diff.altas == []
    assert diff.cambios == []
    assert diff.bajas == []


def test_numero_incidente_duplicado_remoto_es_ambiguo() -> None:
    local = _local(numero_incidente="838937")
    remoto1 = _remoto(numero_incidente="838937-1")
    remoto2 = _remoto(numero_incidente="838937-9")
    diff = reconciliar_incidentes([local], [remoto1, remoto2])
    assert diff.ambiguos == 1
    assert diff.altas == []
    assert diff.cambios == []
    assert diff.bajas == []


def test_ambas_listas_vacias() -> None:
    diff = reconciliar_incidentes([], [])
    assert diff.altas == diff.bajas == diff.cambios == []
    assert diff.ambiguos == 0


def test_idempotencia_aplicar_el_diff_y_volver_a_diffear_da_cero_cambios() -> None:
    """El test que protege contra ruido de float y asimetría None/"" a la vez:
    aplicar el `cambio` propuesto y re-diffear contra el mismo remoto no debe
    generar un `cambio` nuevo."""
    local = _local(costo_servicio_cobrado=1000.0, empresa_nombre="Vieja")
    remoto = _remoto(costo_servicio_cobrado=1500.0, empresa_nombre="Nueva")
    diff = reconciliar_incidentes([local], [remoto])
    [cambio] = diff.cambios

    actualizado = Incidente(
        id=local.id,
        liquidacion_id=local.liquidacion_id,
        numero_incidente=local.numero_incidente,
        rubro=cambio.rubro,
        tipo=cambio.tipo,
        empresa_nombre=cambio.empresa_nombre,
        sucursal_nombre=cambio.sucursal_nombre,
        nro_serie=cambio.nro_serie,
        fecha_cierre=cambio.fecha_cierre,
        costo_servicio_cobrado=cambio.costo_servicio_cobrado,
        cant_km_cobrado=cambio.cant_km_cobrado,
        costo_km_cobrado=cambio.costo_km_cobrado,
        total_viaje_cobrado=cambio.total_viaje_cobrado,
        costo_total_cobrado=cambio.costo_total_cobrado,
        pasa_it=cambio.pasa_it,
        costo_servicio_esperado=None,
        cant_km_esperado=None,
        costo_km_esperado=None,
        estado_validacion="pendiente",
    )

    diff2 = reconciliar_incidentes([actualizado], [remoto])
    assert diff2.cambios == []
    assert diff2.altas == []
    assert diff2.bajas == []
