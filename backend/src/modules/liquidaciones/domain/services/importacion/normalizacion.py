"""Normalización del tipo de servicio en texto libre (columna "Tipo" de la tabla
exportada) al vocabulario de `Tarifario.tipo_servicio` — puerto de `_normalizar_tipo`
del legacy, mismo orden de precedencia (instalación/pre-correctivo antes que
correctivo, porque ambos textos suelen contener "correctivo" como substring)."""

from src.modules.liquidaciones.domain.entities.tarifario import (
    TIPO_CORRECTIVO,
    TIPO_GUARDIA,
    TIPO_INSTALACION_DESINSTALACION,
    TIPO_PRE_CORRECTIVO,
    TIPO_PREVENTIVO,
    TIPO_SISTEMAS,
)


def normalizar_tipo_servicio(crudo: str) -> str:
    texto = crudo.lower().strip()
    if "instalacion" in texto or "instalación" in texto or "desinstal" in texto:
        return TIPO_INSTALACION_DESINSTALACION
    if "pre-correctivo" in texto or "pre correctivo" in texto or "preco" in texto:
        return TIPO_PRE_CORRECTIVO
    if "preventivo" in texto:
        return TIPO_PREVENTIVO
    if "correctivo" in texto:
        return TIPO_CORRECTIVO
    if "guardia" in texto:
        return TIPO_GUARDIA
    if "sistema" in texto:
        return TIPO_SISTEMAS
    return texto or TIPO_CORRECTIVO
