"""Errores del módulo de vacaciones. Los códigos HTTP replican al legacy
VacaSync: 400 para reglas de datos (saldo, año, ciclo), 409 para conflictos de
concurrencia de agenda (solape, exclusión, límite por cargo), 403/404 según
corresponda.
"""

from typing import ClassVar
from uuid import UUID

from src.shared.domain.errors import (
    ApplicationError,
    BusinessRuleViolationError,
    DomainError,
    NotFoundError,
)


class OperacionNoPermitidaError(ApplicationError):
    http_status: ClassVar[int] = 403
    default_code: ClassVar[str] = "FORBIDDEN"


class EmpleadoNoEncontradoError(NotFoundError):
    def __init__(self, empleado_id: UUID) -> None:
        super().__init__(f"Empleado {empleado_id} no encontrado")


class SolicitudNoEncontradaError(NotFoundError):
    def __init__(self, solicitud_id: UUID) -> None:
        super().__init__(f"Solicitud {solicitud_id} no encontrada")


class EmpleadoInactivoError(DomainError):
    default_code: ClassVar[str] = "EMPLEADO_INACTIVO"

    def __init__(self, message: str = "El empleado está inactivo") -> None:
        super().__init__(message)


class RangoSinDiasError(DomainError):
    default_code: ClassVar[str] = "RANGO_SIN_DIAS"

    def __init__(self) -> None:
        super().__init__("El rango no contiene días laborables")


class AnioPasadoError(DomainError):
    default_code: ClassVar[str] = "ANIO_PASADO"

    def __init__(self) -> None:
        super().__init__("No se pueden registrar vacaciones en años pasados")


class AnioMuyLejanoError(DomainError):
    default_code: ClassVar[str] = "ANIO_MUY_LEJANO"

    def __init__(self) -> None:
        super().__init__("No se pueden solicitar vacaciones con más de un año de anticipación")


class AdelantoNoHabilitadoError(DomainError):
    default_code: ClassVar[str] = "ADELANTO_NO_HABILITADO"

    def __init__(self) -> None:
        super().__init__("Las solicitudes adelantadas al año siguiente no están habilitadas")


class CicloAunNoAbiertoError(DomainError):
    default_code: ClassVar[str] = "CICLO_AUN_NO_ABIERTO"

    def __init__(self, target_year: int, fecha_apertura: str) -> None:
        super().__init__(
            f"El ciclo {target_year} aún no está abierto. Se habilitará el {fecha_apertura}"
        )


class CicloNoHabilitadoError(DomainError):
    default_code: ClassVar[str] = "CICLO_NO_HABILITADO"

    def __init__(self, target_year: int) -> None:
        super().__init__(f"El ciclo {target_year} no está habilitado para recibir solicitudes")


class SaldoInsuficienteError(DomainError):
    default_code: ClassVar[str] = "SALDO_INSUFICIENTE"

    def __init__(self, dias: int, disponibles: int) -> None:
        super().__init__(
            f"Saldo insuficiente: solicita {dias} días pero sólo dispone de {disponibles}"
        )


class LimiteAdelantoError(DomainError):
    default_code: ClassVar[str] = "LIMITE_ADELANTO"

    def __init__(self, max_advance_days: int, target_year: int) -> None:
        super().__init__(
            f"Límite de solicitudes adelantadas: sólo se permiten {max_advance_days} "
            f"días anticipados del año {target_year}"
        )


class SoloPendientesEditablesError(DomainError):
    default_code: ClassVar[str] = "SOLO_PENDIENTES_EDITABLES"

    def __init__(self, accion: str) -> None:
        super().__init__(f"Sólo puedes {accion} solicitudes pendientes")


class SolapamientoPropioError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "SOLAPAMIENTO_PROPIO"

    def __init__(self) -> None:
        super().__init__("Ya existe una solicitud que se solapa con esas fechas")


class ExclusionMutuaError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "EXCLUSION_MUTUA"

    def __init__(self, nombre_contraparte: str) -> None:
        super().__init__(
            "No se pueden solicitar vacaciones en estas fechas debido a una regla "
            f"de exclusión mutua con {nombre_contraparte}."
        )


class LimiteCargoError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "LIMITE_CARGO"

    def __init__(self, nombre_cargo: str, limite: int) -> None:
        super().__init__(
            f"Se supera el límite máximo de empleados de la posición '{nombre_cargo}' "
            f"tomándose vacaciones al mismo tiempo (Límite: {limite})."
        )


class AusenciaNoEncontradaError(NotFoundError):
    def __init__(self, ausencia_id: UUID) -> None:
        super().__init__(f"Baja {ausencia_id} no encontrada")


class SoloAusenciasPendientesError(DomainError):
    default_code: ClassVar[str] = "SOLO_PENDIENTES_EDITABLES"

    def __init__(self, accion: str) -> None:
        super().__init__(f"Sólo puedes {accion} bajas pendientes")


class SolapamientoAusenciaError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "SOLAPAMIENTO_AUSENCIA"

    def __init__(self) -> None:
        super().__init__("Ya existe una baja del mismo tipo que se solapa con esas fechas")


class SolapamientoConVacacionesError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "SOLAPAMIENTO_VACACIONES"

    def __init__(self) -> None:
        super().__init__(
            "Ya existe una solicitud de vacaciones que se solapa con esas fechas"
        )


class SectorConEmpleadosError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "SECTOR_CON_EMPLEADOS"

    def __init__(self) -> None:
        super().__init__("No se puede eliminar un sector con empleados asignados")


class CargoConEmpleadosError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "CARGO_CON_EMPLEADOS"

    def __init__(self) -> None:
        super().__init__("No se puede eliminar un cargo con empleados asignados")


class NombreDuplicadoError(BusinessRuleViolationError):
    default_code: ClassVar[str] = "NOMBRE_DUPLICADO"

    def __init__(self, campo: str, valor: str) -> None:
        super().__init__(f"Ya existe un registro con {campo} {valor!r}")
