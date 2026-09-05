from dataclasses import replace
from datetime import date

from src.modules.contadores.domain.services.estimacion.recesos import recesos_aplicables
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef
from src.modules.contadores.domain.value_objects.estimacion.promedio_parque import PromedioParque
from src.modules.contadores.domain.value_objects.estimacion.receso_cliente import RecesoCliente

FECHA_OBJETIVO_DEFAULT = date(2026, 4, 30)

_BASE = EstimacionInput(
    pendiente_estimar=True,
    fecha_objetivo=FECHA_OBJETIVO_DEFAULT,
    periodo_desde=date(2026, 4, 1),
    periodo_hasta=date(2026, 5, 1),
    estado_maquina="NORMAL",
    tecnologia="MONO",
    velocidad_ppm=45.0,
    ultimo_contador_facturado=LecturaRef(0, date(2026, 1, 1), 1),
    ultimo_real=None,
    fecha_ultimo_real_no_t4=None,
    real_anterior=None,
    t4_mas_reciente=None,
    t4_revisado=False,
    parque_cliente_modelo=None,
    parque_grupo_modelo=None,
    parque_cliente_tecnologia=None,
    parque_global_modelo=None,
    prom_6_facturados=None,
    id_grupo_economico=1,
    id_anexo=1,
    recesos=[],
)


def lectura(valor: float, fecha: date, tipo_toma: int = 1) -> LecturaRef:
    return LecturaRef(valor, fecha, tipo_toma)


def parque(valor: float, n_equipos: int = 8, **kwargs: float | None) -> PromedioParque:
    return PromedioParque(valor=valor, n_equipos=n_equipos, **kwargs)  # type: ignore[arg-type]


def receso(
    desde: date, hasta: date, id_grupo_economico: int = 1, id_anexo: int | None = 1
) -> RecesoCliente:
    return RecesoCliente(desde, hasta, id_grupo_economico, id_anexo)


def make_input(**overrides: object) -> EstimacionInput:
    return replace(_BASE, **overrides)  # type: ignore[arg-type]


def make_ctx(entrada: EstimacionInput) -> ContextoEstimacion:
    recesos = recesos_aplicables(entrada.recesos, entrada.id_anexo, entrada.id_grupo_economico)
    return ContextoEstimacion(entrada, recesos)
