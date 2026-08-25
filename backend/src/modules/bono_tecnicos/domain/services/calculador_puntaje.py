"""Fórmula de Puntaje de "Tecnicos.xlsx" (celda `Lista!$J$9`):

    Puntaje = (Correctivo + InstDes + EntregaInsumos + TV
               + Preventivo*0.65 + PreCorrectivo*0.5) / Días

Pesos y estructura literales del archivo original (ver memoria de proyecto
`project-bono-tecnicos-analisis`) — no "mejorar" los coeficientes sin que el
usuario lo pida explícitamente."""

from src.modules.bono_tecnicos.domain.entities.conteo_tecnico import ConteoTecnico

_PESO_PREVENTIVO = 0.65
_PESO_PRE_CORRECTIVO = 0.5
_DECIMALES = 2


def calcular_puntaje(conteo: ConteoTecnico, dias: float, tareas_varias: int) -> float | None:
    """`None` cuando Días es 0 o negativo: el Excel nunca contempla ese caso
    (siempre tenía un valor cargado a mano) y dividir daría un resultado sin
    sentido de negocio en vez de una regla real — se lo dejamos sin puntaje
    a la UI en lugar de inventar un 0 o un error."""
    if dias <= 0:
        return None

    numerador = (
        conteo.correctivo
        + conteo.inst_des
        + conteo.entrega_insumos
        + tareas_varias
        + conteo.preventivo * _PESO_PREVENTIVO
        + conteo.pre_correctivo * _PESO_PRE_CORRECTIVO
    )
    return round(numerador / dias, _DECIMALES)
