from src.shared.domain.errors import BusinessRuleViolationError, NotFoundError, ValidationError


class InvalidMeterSourceError(ValidationError):
    default_code = "INVALID_METER_SOURCE"

    def __init__(self, raw_value: str) -> None:
        super().__init__(f"Fuente de contador inválida: {raw_value!r} (debe ser 'sds' o 'ers')")


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
