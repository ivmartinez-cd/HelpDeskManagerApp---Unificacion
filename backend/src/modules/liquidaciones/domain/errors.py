from typing import ClassVar
from uuid import UUID

from src.shared.domain.errors import BusinessRuleViolationError, NotFoundError, ValidationError


class LiquidacionNoEncontradaError(NotFoundError):
    default_code: ClassVar[str] = "LIQUIDACION_NO_ENCONTRADA"

    def __init__(self, liquidacion_id: UUID) -> None:
        super().__init__(f"Liquidación no encontrada: {liquidacion_id}")


class PrestadorNoEncontradoError(NotFoundError):
    default_code: ClassVar[str] = "PRESTADOR_NO_ENCONTRADO"

    def __init__(self, prestador_id: UUID) -> None:
        super().__init__(f"Prestador no encontrado: {prestador_id}")


class SpstNoEncontradoError(NotFoundError):
    default_code: ClassVar[str] = "SPST_NO_ENCONTRADO"

    def __init__(self, spst_id: UUID) -> None:
        super().__init__(f"SPST no encontrado: {spst_id}")


class TarifarioNoEncontradoError(NotFoundError):
    default_code: ClassVar[str] = "TARIFARIO_NO_ENCONTRADO"

    def __init__(self, tarifario_id: UUID) -> None:
        super().__init__(f"Tarifario no encontrado: {tarifario_id}")


class TablaKmNoEncontradaError(NotFoundError):
    default_code: ClassVar[str] = "TABLA_KM_NO_ENCONTRADA"

    def __init__(self, tabla_km_id: UUID) -> None:
        super().__init__(f"Entrada de Tabla KM no encontrada: {tabla_km_id}")


class AcuerdoPrecioNoEncontradoError(NotFoundError):
    default_code: ClassVar[str] = "ACUERDO_PRECIO_NO_ENCONTRADO"

    def __init__(self, acuerdo_id: UUID) -> None:
        super().__init__(f"Acuerdo de precio no encontrado: {acuerdo_id}")


class AcuerdoPrecioInvalidoError(ValidationError):
    default_code: ClassVar[str] = "ACUERDO_PRECIO_INVALIDO"


class KmReferenciaInvalidoError(ValidationError):
    default_code: ClassVar[str] = "KM_REFERENCIA_INVALIDO"


class ParSinTablaKmError(NotFoundError):
    """El par empresa+sucursal no tiene fila en la Tabla KM del prestador — antes de
    asignarle zona hay que darlo de alta (es el caso ALT009)."""

    default_code: ClassVar[str] = "TABLA_KM_PAR_NO_ENCONTRADO"

    def __init__(self, empresa: str, sucursal: str) -> None:
        super().__init__(
            f"'{empresa}' — '{sucursal}' no está en la Tabla KM del prestador; "
            "cargá la sucursal antes de asignarle zona"
        )


class PrestadorConLiquidacionesError(BusinessRuleViolationError):
    """`liquidaciones.prestador_id` no tiene `ondelete` a propósito (ver
    `infrastructure/models/liquidacion_model.py`) — es historial de facturación
    real, no se pierde por una baja administrativa. Se traduce el
    `IntegrityError` de Postgres acá, en el repositorio, para no propagar un 500
    crudo."""

    default_code: ClassVar[str] = "PRESTADOR_CON_LIQUIDACIONES"

    def __init__(self, prestador_id: UUID) -> None:
        super().__init__(
            f"No se puede eliminar el prestador {prestador_id}: tiene liquidaciones "
            "asociadas. Desactivalo en su lugar."
        )


class PrestadorDuplicadoError(BusinessRuleViolationError):
    """`nombre_corto` es UNIQUE en `prestadores`: es la clave con la que matchean
    los CSV de liquidación. El caso de uso lo chequea antes de escribir y el
    repositorio traduce el `IntegrityError` por si dos altas corren a la vez."""

    default_code: ClassVar[str] = "PRESTADOR_DUPLICADO"

    def __init__(self, nombre_corto: str) -> None:
        super().__init__(
            f"Ya existe un prestador con el nombre corto '{nombre_corto}'. "
            "Elegí otro o editá el existente."
        )


class TarifarioInvalidoError(ValidationError):
    default_code: ClassVar[str] = "TARIFARIO_INVALIDO"


class CdVinculoDuplicadoError(BusinessRuleViolationError):
    """El UNIQUE de `cd_prestador_id` garantiza que un prestador de CD vincule
    a lo sumo una fila local — IntegrityError traducido acá (mismo criterio que
    `SigesVinculoDuplicadoError`)."""

    default_code: ClassVar[str] = "CD_VINCULO_DUPLICADO"

    def __init__(self, cd_prestador_id: int | None) -> None:
        super().__init__(
            f"El prestador {cd_prestador_id} de Canal Directo ya está vinculado a otro "
            "prestador del catálogo. Desvinculalo primero."
        )


class SigesVinculoDuplicadoError(BusinessRuleViolationError):
    """El UNIQUE de `siges_empresa_id` (prestadores/spsts) garantiza que una
    empresa de Siges vincule a lo sumo una fila local — el `IntegrityError` se
    traduce acá para no propagar un 500 crudo (mismo criterio que
    `PrestadorConLiquidacionesError`)."""

    default_code: ClassVar[str] = "SIGES_VINCULO_DUPLICADO"

    def __init__(self, siges_empresa_id: int | None) -> None:
        super().__init__(
            f"La empresa {siges_empresa_id} de Siges ya está vinculada a otra fila "
            "del catálogo. Desvinculala primero."
        )


class PrestadorSinVinculoSigesError(BusinessRuleViolationError):
    """El alta asistida y los syncs del ADR-014 solo operan sobre prestadores
    con `siges_empresa_id` — pedirlos para uno sin vincular es un error de uso,
    no un caso silencioso."""

    default_code: ClassVar[str] = "PRESTADOR_SIN_VINCULO_SIGES"

    def __init__(self, prestador_id: UUID) -> None:
        super().__init__(
            f"El prestador {prestador_id} no está vinculado a Siges. Vinculalo desde "
            "la pantalla de Prestadores antes de usar el alta asistida."
        )


class PrestadorSinBaseSucursalError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "PRESTADOR_SIN_BASE_SUCURSAL"

    def __init__(self, prestador_id: UUID) -> None:
        super().__init__(
            f"El prestador {prestador_id} no tiene sucursal base configurada. "
            "Configurala desde la pantalla de Prestadores antes de calcular distancias."
        )


class BaseSucursalSinCoordenadasError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "BASE_SUCURSAL_SIN_COORDENADAS"

    def __init__(self, siges_sucursal_id: int) -> None:
        super().__init__(
            f"La sucursal base {siges_sucursal_id} no tiene coordenadas cargadas en Siges. "
            "Cargá latitud y longitud en Gestión antes de calcular distancias."
        )


class PreviewNoEncontradoError(NotFoundError):
    """El apply exige un preview vigente: si se corrió otro preview después (o
    se aplicó), el id viejo ya no existe — obliga a re-previsualizar en vez de
    aplicar una propuesta que el usuario no vio."""

    default_code: ClassVar[str] = "PREVIEW_NO_ENCONTRADO"

    def __init__(self, preview_id: UUID) -> None:
        super().__init__(
            f"Preview de cálculo no encontrado: {preview_id}. "
            "Volvé a previsualizar antes de aplicar."
        )


class SucursalCoordenadasNoEncontradaError(NotFoundError):
    default_code: ClassVar[str] = "SUCURSAL_COORDENADAS_NO_ENCONTRADA"

    def __init__(self, siges_sucursal_id: int) -> None:
        super().__init__(
            f"No hay resolución de coordenadas para la sucursal Siges {siges_sucursal_id}. "
            "Corré 'Geocodificar faltantes' primero."
        )


class FilaSinCoordenadasError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "FILA_SIN_COORDENADAS"

    def __init__(self, tabla_km_id: UUID) -> None:
        super().__init__(
            f"La fila {tabla_km_id} de Tabla KM no tiene coordenadas de destino. "
            "Resolvelas con 'Buscar lugar' o cargalas a mano antes de recalcular."
        )


class FilaSinDomicilioError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "FILA_SIN_DOMICILIO"

    def __init__(self, tabla_km_id: UUID) -> None:
        super().__init__(
            f"La fila {tabla_km_id} de Tabla KM no tiene domicilio ni localidad del "
            "cliente — no hay nada que geocodificar."
        )


class TopeLlamadasGoogleError(BusinessRuleViolationError):
    """Control de costo: la key es corporativa y paga. Antes que pasarse del
    tope configurado, la corrida se corta y lo reporta."""

    default_code: ClassVar[str] = "TOPE_LLAMADAS_GOOGLE"

    def __init__(self, necesarias: int, tope: int) -> None:
        super().__init__(
            f"El cálculo necesita {necesarias} llamadas a Google y el tope por corrida "
            f"es {tope} (GOOGLE_MAPS_MAX_CALLS_PER_RUN). Subí el tope o reducí el alcance."
        )


class ArchivoLiquidacionInvalidoError(ValidationError):
    """El archivo no se pudo leer como tabla, o ninguna tabla tiene una columna de
    incidente reconocible — mismo `ValueError` que el legacy convertía en 400."""

    default_code: ClassVar[str] = "ARCHIVO_LIQUIDACION_INVALIDO"

    def __init__(self, detalle: str) -> None:
        super().__init__(f"No se pudo leer el archivo de liquidación: {detalle}")


class ArchivoMaestroInvalidoError(ValidationError):
    """El archivo no se pudo leer como Excel, o ninguna hoja tiene una celda
    "AGENTE:" reconocible — mismo caso que el legacy convertía en 422 (acá 400,
    convención del monorepo para `ValidationError`)."""

    default_code: ClassVar[str] = "ARCHIVO_MAESTRO_INVALIDO"

    def __init__(self, detalle: str) -> None:
        super().__init__(f"No se pudo leer el archivo maestro de prestador: {detalle}")


class IncidenteRelacionadoInvalidoError(ValidationError):
    """El incidente que la TL elige como "vínculo de ruta compartida" al
    gestionar una alerta tiene que pertenecer a la misma liquidación — evita
    vincular contra un incidente de otro prestador o período por error de UI."""

    default_code: ClassVar[str] = "INCIDENTE_RELACIONADO_INVALIDO"

    def __init__(self, incidente_id: UUID) -> None:
        super().__init__(f"El incidente {incidente_id} no pertenece a esta liquidación.")


class SincronizacionEnProgresoError(BusinessRuleViolationError):
    """Ya hay una sincronización con Canal Directo en curso (advisory lock tomado) —
    el caller no debe reintentar; la sincronización en progreso terminará sola.
    Incidente real 2026-09-01: dos pestañas disparando `/sincronizar` a la vez
    crearon liquidaciones duplicadas (mismo `numero_liquidacion`, sin constraint
    que lo impidiera) porque cada request leía el set de existentes antes de que
    el otro comiteara sus creates."""

    default_code: ClassVar[str] = "SINCRONIZACION_EN_PROGRESO"

    def __init__(self) -> None:
        super().__init__("Ya hay una sincronización con Canal Directo en curso")


class AlertasNoEncontradasError(NotFoundError):
    """Alguna de las alertas que la TL gestiona en lote no pertenece a la
    liquidación (o ya no existe tras un re-análisis). Se rechaza el lote entero
    antes de tocar nada: la TL espera que el mismo motivo aplique a todas."""

    default_code: ClassVar[str] = "ALERTAS_NO_ENCONTRADAS"

    def __init__(self, alerta_ids: list[UUID]) -> None:
        super().__init__(
            f"{len(alerta_ids)} alerta(s) no pertenecen a esta liquidación: "
            + ", ".join(str(a) for a in alerta_ids[:5])
        )
