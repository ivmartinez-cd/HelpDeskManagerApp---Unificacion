from typing import ClassVar

from src.shared.domain.errors import (
    ApplicationError,
    BusinessRuleViolationError,
    NotFoundError,
    ValidationError,
)


class InvalidMeterSourceError(ValidationError):
    default_code = "INVALID_METER_SOURCE"

    def __init__(self, raw_value: str) -> None:
        super().__init__(f"Fuente de contador inválida: {raw_value!r} (debe ser 'sds' o 'ers')")


class GrupoEconomicoSinFtpError(BusinessRuleViolationError):
    default_code = "GRUPO_ECONOMICO_SIN_FTP"

    def __init__(self, grupo_id: int) -> None:
        super().__init__(
            f"El grupo económico {grupo_id} no tiene usuario y contraseña FTP cargados en Siges"
        )


class FtpGrupoEconomicoRequeridoError(ValidationError):
    default_code = "FTP_GRUPO_ECONOMICO_REQUERIDO"

    def __init__(self) -> None:
        super().__init__("Elegí el grupo económico de Siges del que salen usuario y contraseña")


class FtpClientNotFoundError(NotFoundError):
    default_code = "FTP_CLIENT_NOT_FOUND"

    def __init__(self) -> None:
        super().__init__("Cliente FTP no encontrado")


class DuplicateFtpClientNameError(BusinessRuleViolationError):
    default_code = "DUPLICATE_FTP_CLIENT_NAME"

    def __init__(self, name: str) -> None:
        super().__init__(f"Ya existe un cliente FTP con el nombre {name!r}")


class InvalidCounterWorkbookError(ValidationError):
    default_code = "INVALID_COUNTER_WORKBOOK"


class InvalidDateRangeError(ValidationError):
    default_code = "INVALID_DATE_RANGE"

    def __init__(self) -> None:
        super().__init__("La fecha final debe ser posterior a la fecha inicial")


class EmptyCounterWorkbookError(ValidationError):
    default_code = "EMPTY_COUNTER_WORKBOOK"

    def __init__(self) -> None:
        super().__init__(
            "El archivo no contiene registros válidos (todas las filas tienen "
            "Fecha o Contador nulos/inválidos)"
        )


class MissingColumnError(ValidationError):
    default_code = "MISSING_COLUMN"

    def __init__(self, column: str) -> None:
        super().__init__(f"No se encontró la columna requerida {column!r} en el archivo")


class NoFaltaContadorRowsError(ValidationError):
    default_code = "NO_FALTA_CONTADOR_ROWS"

    def __init__(self) -> None:
        super().__init__("No se encontraron filas con Tipo conteniendo 'FALTA CONTADOR'")


class EmptyDb3ExportError(ValidationError):
    default_code = "EMPTY_DB3_EXPORT"

    def __init__(self, warnings: list[str]) -> None:
        detalle = "; ".join(warnings) if warnings else "sin detalle"
        super().__init__(f"No se obtuvieron datos de los DB3 provistos: {detalle}")


class AsignacionOverrideNotFoundError(NotFoundError):
    default_code = "ASIGNACION_OVERRIDE_NOT_FOUND"

    def __init__(self) -> None:
        super().__init__("Override de asignación no encontrado")


class InvalidOverrideRangeError(ValidationError):
    default_code = "INVALID_OVERRIDE_RANGE"

    def __init__(self) -> None:
        super().__init__("El rango de vigencia del override es inválido (desde > hasta)")


class OverrideMismoOperadorError(ValidationError):
    default_code = "OVERRIDE_MISMO_OPERADOR"

    def __init__(self) -> None:
        super().__init__("El operador ausente y el reemplazante no pueden ser el mismo")


class OperadorNoEncontradoError(ValidationError):
    default_code = "OPERADOR_NO_ENCONTRADO"

    def __init__(self, username: str) -> None:
        super().__init__(
            f"El operador {username!r} no existe en el catálogo local de operadores "
            "(¿typo en el username de Gestión?)"
        )


class OverrideNoEditableError(BusinessRuleViolationError):
    default_code = "OVERRIDE_NO_EDITABLE"

    def __init__(self) -> None:
        super().__init__(
            "Solo se puede editar un override activo — uno cancelado es un registro histórico"
        )


class OverlappingOverrideError(BusinessRuleViolationError):
    default_code = "OVERLAPPING_OVERRIDE"

    def __init__(self) -> None:
        super().__init__(
            "Ya existe un override activo para ese operador ausente con fechas superpuestas "
            "y alcance en común"
        )


class ClienteNuevoNotFoundError(NotFoundError):
    default_code = "CLIENTE_NUEVO_NOT_FOUND"

    def __init__(self) -> None:
        super().__init__("Ficha de cliente nuevo no encontrada")


class DuplicateClienteNuevoError(BusinessRuleViolationError):
    default_code = "DUPLICATE_CLIENTE_NUEVO"

    def __init__(self, cliente: str) -> None:
        super().__init__(f"Ya existe una ficha abierta para el cliente {cliente!r}")


class InvalidClienteNuevoError(ValidationError):
    default_code = "INVALID_CLIENTE_NUEVO"


class InvalidEstadoClienteNuevoError(ValidationError):
    default_code = "INVALID_ESTADO_CLIENTE_NUEVO"

    def __init__(self, estado: str) -> None:
        super().__init__(f"Estado de ficha inválido: {estado!r}")


class ProcesoNoEncontradoError(NotFoundError):
    default_code = "PROCESO_NO_ENCONTRADO"

    def __init__(self, nro_proceso: int) -> None:
        super().__init__(f"No se encontró el proceso {nro_proceso} en Siges")


class RecesoRangoInvalidoError(ValidationError):
    default_code = "RECESO_RANGO_INVALIDO"

    def __init__(self) -> None:
        super().__init__("El receso debe terminar el mismo día que empieza o después")


class FilaProyeccionInexistenteError(NotFoundError):
    default_code = "FILA_PROYECCION_INEXISTENTE"

    def __init__(self) -> None:
        super().__init__("Equipo o clase no encontrado en el proceso")


class AccionProyeccionInvalidaError(ApplicationError):
    """La acción del operador no aplica a esa fila o a esa selección (422, como
    respondía el router antes de moverse a application)."""

    http_status: ClassVar[int] = 422
    default_code = "ACCION_PROYECCION_INVALIDA"
