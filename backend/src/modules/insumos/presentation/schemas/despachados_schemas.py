"""Schemas de Insumos > Despachados: tabla, tarjetas, estado de la actualización y
acciones. Contrato camelCase como el resto de insumos (acá con un `alias_generator` que
solo toca la serialización, en vez de un `serialization_alias` por campo); fechas ISO
(`date` -> "2026-09-24", `datetime` aware -> "2026-09-24T15:00:00Z")."""

from datetime import date, datetime

from pydantic import AliasGenerator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from src.modules.insumos.application.dtos.despachados import (
    EstadoActualizacion,
    TarjetasDespachos,
)
from src.modules.insumos.domain.entities.despachados.accion_registrada import (
    AccionRegistrada,
    ResultadoAccion,
    TipoAccion,
)
from src.modules.insumos.domain.entities.despachados.corrida import Corrida, OrigenCorrida
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from src.modules.insumos.domain.value_objects.despachados.vista_despachos import (
    FilaDespacho,
    UltimaAccion,
)


class CamelOut(BaseModel):
    """Base de las respuestas: los campos salen en camelCase."""

    model_config = ConfigDict(alias_generator=AliasGenerator(serialization_alias=to_camel))


class UltimaAccionOut(CamelOut):
    tipo: TipoAccion
    resultado: ResultadoAccion
    usuario_nombre: str
    creada_en: datetime

    @classmethod
    def from_ultima(cls, accion: UltimaAccion) -> "UltimaAccionOut":
        return cls(
            tipo=accion.tipo,
            resultado=accion.resultado,
            usuario_nombre=accion.usuario_nombre,
            creada_en=accion.creada_en,
        )


class FilaDespachoOut(CamelOut):
    guia: str
    color: ColorSemaforo
    alerta_abierta: bool
    observacion: str
    fecha_limite: date | None
    dias_habiles_para_limite: int | None
    estado: str
    motivo: str
    sucursal_oca: str
    fecha_estado: date | None
    operativa: str
    cliente: str
    fecha_remito: date
    numero_remito: int | None
    cantidad_remitos: int
    incidente: str
    cantidad_incidentes: int
    ultima_accion: UltimaAccionOut | None
    con_error: bool

    @classmethod
    def from_fila(cls, fila: FilaDespacho) -> "FilaDespachoOut":
        """Mismos campos que la fila del dominio; la última acción, anidada."""
        ultima = fila.ultima_accion
        datos = {c: getattr(fila, c) for c in cls.model_fields if c != "ultima_accion"}
        return cls(
            **datos,
            ultima_accion=None if ultima is None else UltimaAccionOut.from_ultima(ultima),
        )


class ResumenOut(CamelOut):
    por_color: dict[ColorSemaforo, int]
    """Claves: los valores de `ColorSemaforo` ("verde", "rojo", …), todas presentes."""
    alertas_rojas: int
    alertas_naranjas: int
    naranjas_sin_accion: int
    limite_mas_proximo: date | None
    dias_habiles_limite_mas_proximo: int | None
    operativas: list[str]

    @classmethod
    def from_tarjetas(cls, tarjetas: TarjetasDespachos) -> "ResumenOut":
        resumen = tarjetas.resumen
        return cls(
            por_color=dict(resumen.por_color),
            alertas_rojas=resumen.alertas_rojas,
            alertas_naranjas=resumen.alertas_naranjas,
            naranjas_sin_accion=resumen.naranjas_sin_accion,
            limite_mas_proximo=resumen.limite_mas_proximo,
            dias_habiles_limite_mas_proximo=tarjetas.dias_habiles_limite_mas_proximo,
            operativas=list(resumen.operativas),
        )


class CorridaOut(CamelOut):
    id: int
    origen: OrigenCorrida
    usuario_nombre: str | None
    iniciada_en: datetime
    terminada_en: datetime | None
    envios_nuevos: int
    consultas_ok: int
    consultas_error: int
    error: str | None

    @classmethod
    def from_corrida(cls, corrida: Corrida) -> "CorridaOut":
        resumen = corrida.resumen
        return cls(
            id=corrida.id,
            origen=corrida.origen,
            usuario_nombre=corrida.usuario_nombre,
            iniciada_en=corrida.iniciada_en,
            terminada_en=corrida.terminada_en,
            envios_nuevos=resumen.envios_nuevos,
            consultas_ok=resumen.consultas_ok,
            consultas_error=resumen.consultas_error,
            error=resumen.error,
        )


class EstadoActualizacionOut(CamelOut):
    en_curso: bool
    iniciada_en: datetime | None
    """Cuándo arrancó la corrida en curso; None si no hay ninguna corriendo."""
    ultima_terminada: CorridaOut | None

    @classmethod
    def from_estado(cls, estado: EstadoActualizacion) -> "EstadoActualizacionOut":
        en_curso = estado.ultima if estado.en_curso else None
        terminada = estado.ultima_terminada
        return cls(
            en_curso=estado.en_curso,
            iniciada_en=None if en_curso is None else en_curso.iniciada_en,
            ultima_terminada=None if terminada is None else CorridaOut.from_corrida(terminada),
        )


class ActualizacionLanzadaOut(CamelOut):
    en_curso: bool = True


class AccionIn(BaseModel):
    """El detalle se valida en el caso de uso (vacío o de más de 2000 caracteres -> 400
    `ACCION_DESPACHO_INVALIDA`)."""

    model_config = ConfigDict(populate_by_name=True)

    tipo: TipoAccion
    detalle: str
    resultado: ResultadoAccion
    cerrar_alerta: bool = Field(default=False, alias="cerrarAlerta")


class AccionOut(CamelOut):
    id: int
    guia: str
    tipo: TipoAccion
    detalle: str
    resultado: ResultadoAccion
    cerro_alerta: bool
    usuario_nombre: str
    creada_en: datetime

    @classmethod
    def from_accion(cls, accion: AccionRegistrada) -> "AccionOut":
        return cls(
            id=accion.id,
            guia=accion.guia,
            tipo=accion.tipo,
            detalle=accion.detalle,
            resultado=accion.resultado,
            cerro_alerta=accion.cerro_alerta,
            usuario_nombre=accion.usuario_nombre,
            creada_en=accion.creada_en,
        )
