"""ALT002 — KMs Incorrectos: kilómetros cobrados vs. Tabla KM, con supresión de falso
positivo cuando el tramo es una ruta compartida (otro incidente del mismo día/corredor
ya cobró el km, y este vino en $0 a propósito).

La comparación acepta dos formas válidas de facturar un km decimal de la Tabla KM
(ej. 20.5 km medidos): el entero superior (`math.ceil`, lo habitual — P1, commit
1b562e4) o el valor tal cual está en la tabla. La tolerancia se aplica contra ambos
y alcanza con que una pase: comparar solo contra el ceil convertía en alerta el caso
"PST factura el piso/decimal exacto" que la tolerancia original siempre aceptó
(hallazgo H-4 de la validación 2026-08-13, con contraejemplos reales 71 vs 71.3 y
45 vs 45.4)."""

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
    esperado_raw = tabla_km.kms_a_facturar or 0.0
    esperado = math.ceil(esperado_raw)
    if _dentro_de_tolerancia(cobrado, esperado, esperado_raw, tolerancia_km):
        return []
    if esperado_raw <= 0:
        return [_hallazgo_sin_referencia(incidente, cobrado)]
    if cobrado == 0:
        return _evaluar_sin_km_cobrado(
            incidente, tabla_km, vecinos_mismo_dia, esperado, esperado_raw
        )
    return [_hallazgo(incidente, cobrado, esperado, esperado_raw, [])]


def _evaluar_sin_km_cobrado(
    incidente: Incidente,
    tabla_km: TablaKm,
    vecinos: Sequence[tuple[Incidente, TablaKm | None]],
    esperado: int,
    esperado_raw: float,
) -> list[Hallazgo]:
    """El prestador no cobró km: nunca es un sobrecobro. Solo vale avisar si ese
    mismo día cobró km en otro incidente (posible ruta compartida, para dejar el
    vínculo); si no hay ningún viaje ese día, no hay nada que revisar — hasta
    2026-09-05 esto disparaba "cobró 0 vs 1.560 km" para cada sucursal lejana
    a la que el prestador simplemente no viajó."""
    if _es_ruta_compartida(tabla_km, vecinos):
        return []
    candidatos = _candidatos_ruta(vecinos)
    if not candidatos:
        return []
    return [_hallazgo(incidente, 0.0, esperado, esperado_raw, candidatos)]


def _dentro_de_tolerancia(cobrado: float, esperado: int, esperado_raw: float, tol: float) -> bool:
    return abs(cobrado - esperado) <= tol or abs(cobrado - esperado_raw) <= tol


def _candidatos_ruta(
    vecinos: Sequence[tuple[Incidente, TablaKm | None]],
) -> list[dict[str, object]]:
    """Incidentes del mismo día que sí cobraron km — el "mismo viaje" probable
    cuando este cobró 0 y el corredor no matcheó (la TL lo resolvía a mano como
    "Km asociado a otro incidente")."""
    candidatos: list[dict[str, object]] = []
    for otro, _ in vecinos:
        if (otro.cant_km_cobrado or 0) <= 0:
            continue
        candidatos.append(
            {
                "incidente_id": str(otro.id),
                "numero_incidente": otro.numero_incidente,
                "empresa": otro.empresa_nombre,
                "sucursal": otro.sucursal_nombre,
                "km": otro.cant_km_cobrado,
            }
        )
    return candidatos[:5]


def _hallazgo_sin_referencia(incidente: Incidente, cobrado: float) -> Hallazgo:
    """La fila existe pero nunca se le cargó km: no es "km incorrectos", es
    configuración incompleta — la UI ofrece tomar lo cobrado como referencia."""
    descripcion = (
        f"{incidente.empresa_nombre} — {incidente.sucursal_nombre} no tiene km de "
        f"referencia en Tabla KM; el prestador cobró {cobrado} km"
    )
    contexto = {
        "cobrado": cobrado,
        "esperado": 0,
        "esperado_raw": 0.0,
        "diferencia": round(cobrado, 2),
        "empresa": incidente.empresa_nombre,
        "sucursal": incidente.sucursal_nombre,
        "sin_referencia": True,
    }
    return Hallazgo(descripcion, contexto)


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
    incidente: Incidente,
    cobrado: float,
    esperado: int,
    esperado_raw: float,
    candidatos: list[dict[str, object]],
) -> Hallazgo:
    descripcion = (
        f"KMs cobrados {cobrado} km difieren de la Tabla KM "
        f"({esperado_raw} km → {esperado} km redondeado) "
        f"para {incidente.empresa_nombre} — {incidente.sucursal_nombre}"
    )
    if candidatos:
        descripcion += f"; el mismo día cobró km en #{candidatos[0]['numero_incidente']}"
    return Hallazgo(descripcion, _contexto(incidente, cobrado, esperado, esperado_raw, candidatos))


def _contexto(
    incidente: Incidente,
    cobrado: float,
    esperado: int,
    esperado_raw: float,
    candidatos: list[dict[str, object]],
) -> dict[str, object]:
    contexto: dict[str, object] = {
        "cobrado": cobrado,
        "esperado": esperado,
        "esperado_raw": esperado_raw,
        "diferencia": round(abs(cobrado - esperado), 2),
        "empresa": incidente.empresa_nombre,
        "sucursal": incidente.sucursal_nombre,
    }
    if candidatos:
        contexto["posible_ruta_compartida"] = True
        contexto["candidatos"] = candidatos
    return contexto
