"""ALT002 — KMs Incorrectos: kilómetros cobrados vs. Tabla KM, con supresión de falso
positivo cuando el tramo es una ruta compartida (otro incidente del mismo día/corredor
ya cobró el km, y este vino en $0 a propósito).

La comparación usa math.ceil(kms_a_facturar): la Tabla KM puede tener decimales (ej.
20.5 km medidos) pero el PST factura enteros redondeando hacia arriba. Comparar contra
el entero superior evita falsos positivos cuando el PST cobra ceil(esperado_raw)."""

import math
from collections.abc import Sequence

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.services.motor_reglas._resolucion import mismo_corredor
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import Hallazgo


def evaluar_alt002(
    incidente: Incidente,
    tabla_km: TablaKm | None,
    vecinos_mismo_dia: Sequence[tuple[Incidente, TablaKm | None]],
    tolerancia_km: float,
) -> list[Hallazgo]:
    if tabla_km is None:
        return []
    cobrado = incidente.cant_km_cobrado or 0
    esperado = math.ceil(tabla_km.kms_a_facturar)
    if abs(cobrado - esperado) <= tolerancia_km:
        return []
    if cobrado == 0 and esperado > 0 and _es_ruta_compartida(tabla_km, vecinos_mismo_dia):
        return []
    return [_hallazgo(incidente, cobrado, esperado, tabla_km.kms_a_facturar)]


def _es_ruta_compartida(
    tabla_km: TablaKm, vecinos: Sequence[tuple[Incidente, TablaKm | None]]
) -> bool:
    for otro, tabla_otro in vecinos:
        if (otro.cant_km_cobrado or 0) <= 0 or tabla_otro is None:
            continue
        if mismo_corredor(tabla_km, tabla_otro):
            return True
    return False


def _hallazgo(
    incidente: Incidente, cobrado: float, esperado: int, esperado_raw: float
) -> Hallazgo:
    descripcion = (
        f"KMs cobrados {cobrado} km difieren de la Tabla KM "
        f"({esperado_raw} km → {esperado} km redondeado) "
        f"para {incidente.empresa_nombre} — {incidente.sucursal_nombre}"
    )
    contexto = {
        "cobrado": cobrado,
        "esperado": esperado,
        "esperado_raw": esperado_raw,
        "diferencia": round(abs(cobrado - esperado), 2),
        "empresa": incidente.empresa_nombre,
        "sucursal": incidente.sucursal_nombre,
    }
    return Hallazgo(descripcion, contexto)
