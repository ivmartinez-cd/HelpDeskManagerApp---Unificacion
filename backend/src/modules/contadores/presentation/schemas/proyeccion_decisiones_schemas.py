"""Bodies de las acciones del operador sobre una fila del tablero de
Proyección (`proyeccion_candidatos_router.py`). La selección real
(`nro_proceso`, grupo, anexo, fecha objetivo) viene vacía en el modo ejemplo
y completa en el real. `descartar_hasta` es el mismo corte que recibe el
tablero tras "Descartar y empezar limpio": el panel y las acciones operan
sobre la fila que la grilla muestra (`EquipoEfectivo` del legacy)."""

from datetime import date, datetime

from pydantic import BaseModel

from src.modules.contadores.application.dtos.decision_operador_dto import (
    LecturaElegidaDto,
    ParPartidaLlegadaDto,
)


class SeleccionProcesoSchema(BaseModel):
    nro_proceso: int | None = None
    id_grupo_economico: int | None = None
    id_anexo: int | None = None
    fecha_objetivo: date | None = None
    descartar_hasta: datetime | None = None


class LecturaElegidaSchema(BaseModel):
    """Una lectura del panel de candidatos elegida como Partida o Llegada.
    En el modo real `id_contador` es obligatorio y es lo único que cuenta:
    fecha, valor, tipo y `Para_Facturar` se releen de Siges (el legacy opera
    sobre el `CandidatoContador` de `GetCandidatosAsync`). El resto de los
    campos solo se usa en el modo ejemplo, cuyas lecturas no están en Siges."""

    fecha: date
    valor: float
    tipo_toma: int
    id_contador: int | None = None
    para_facturar: bool = True

    def a_dto(self) -> LecturaElegidaDto:
        return LecturaElegidaDto(
            fecha=self.fecha,
            valor=self.valor,
            tipo_toma=self.tipo_toma,
            id_contador=self.id_contador,
            para_facturar=self.para_facturar,
        )


class RecalcularPLBody(SeleccionProcesoSchema):
    """Vista previa de una P/L manual. Mismos campos planos que el request
    anterior (`RecalcularCandidatoRequest`) más el `ID_Contador` y el
    `Para_Facturar` de cada lectura (este último marca el borde amarillo de
    una Llegada T4 sin revisar)."""

    id_maquina: int
    clase: str
    partida_fecha: date
    partida_valor: float
    partida_tipo_toma: int
    partida_id_contador: int | None = None
    partida_para_facturar: bool = True
    llegada_fecha: date
    llegada_valor: float
    llegada_tipo_toma: int
    llegada_id_contador: int | None = None
    llegada_para_facturar: bool = True

    def par(self) -> ParPartidaLlegadaDto:
        partida = LecturaElegidaDto(
            self.partida_fecha, self.partida_valor, self.partida_tipo_toma,
            self.partida_id_contador, self.partida_para_facturar,
        )
        llegada = LecturaElegidaDto(
            self.llegada_fecha, self.llegada_valor, self.llegada_tipo_toma,
            self.llegada_id_contador, self.llegada_para_facturar,
        )
        return ParPartidaLlegadaDto(self.id_maquina, self.clase, partida, llegada)


class AccionDecisionBody(SeleccionProcesoSchema):
    """`nota`: la observación que el operador tenga escrita al actuar — el
    legacy la graba en la auditoría con "Marcar pendiente" y "Aceptar P/L
    manual" (no con "Aceptar sugerencia"), y no la guarda en la fila."""

    nota: str | None = None

    def nota_limpia(self) -> str | None:
        if self.nota is None or not self.nota.strip():
            return None
        return self.nota.strip()


class AceptarDecisionBody(AccionDecisionBody):
    """Con `partida` y `llegada`: "Aceptar P/L manual". Sin ninguna de las
    dos: "Aceptar sugerencia" (la fila vuelve al cálculo automático)."""

    partida: LecturaElegidaSchema | None = None
    llegada: LecturaElegidaSchema | None = None
