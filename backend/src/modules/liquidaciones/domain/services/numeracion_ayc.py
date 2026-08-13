"""Dígito verificador de la numeración de liquidaciones de AyC — port de
`core/numeracion_ayc.py` del legacy (caracterización §"Dígito verificador
módulo-10"): pesos alternados 3-1-3-1… sobre los dígitos del id de AyC de
izquierda a derecha, dv = (10 - suma % 10) % 10. Número final `"{id}-{dv}"`.

La validación 2026-08-13 (`docs/liquidaciones/VALIDACION_PIPELINE_LIQUIDACIONES_
2026-08-13.md`, hallazgo H-1) confirmó esta fórmula contra los 35 números reales
de la DB (35/35) y contra los ids reales del SOAP (3739↔3739-6, 3922↔3922-4).
El cálculo `id % 10` que reemplaza este módulo solo coincidía en 4/35 — entre
ellos, de casualidad, los dos casos con los que se había validado el ADR-015.
"""

_PESOS = (3, 1)


def digito_verificador(liquidacion_id: int) -> int:
    suma = sum(
        int(digito) * _PESOS[posicion % 2]
        for posicion, digito in enumerate(str(liquidacion_id))
    )
    return (10 - suma % 10) % 10


def numero_liquidacion(liquidacion_id: int) -> str:
    return f"{liquidacion_id}-{digito_verificador(liquidacion_id)}"
