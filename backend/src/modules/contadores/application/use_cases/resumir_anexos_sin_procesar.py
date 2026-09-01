from datetime import datetime

from src.modules.contadores.application.dtos.anexo_sin_procesar import (
    AnexoSinProcesar,
    ResumenAnexosSinProcesar,
)


def resumir_anexos_sin_procesar(
    anexos: list[AnexoSinProcesar], *, consultado_en: datetime
) -> ResumenAnexosSinProcesar:
    """`clientes` cuenta GRUPOS ECONÓMICOS distintos (la unidad de Siges), no
    clientes de Gestión: dos clientes de Gestión que cruzan al mismo grupo
    son un solo cliente para este KPI."""
    return ResumenAnexosSinProcesar(
        clientes=len({a.grupo for a in anexos}),
        anexos=len(anexos),
        consultado_en=consultado_en,
    )
