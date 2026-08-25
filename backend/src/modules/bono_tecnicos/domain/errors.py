import uuid
from typing import ClassVar

from src.shared.domain.errors import NotFoundError, ValidationError


class PeriodoInvalidoError(ValidationError):
    default_code: ClassVar[str] = "PERIODO_INVALIDO"

    def __init__(self, raw_value: int) -> None:
        super().__init__(f"Período inválido (se espera AAAAMM): {raw_value!r}")


class ValorInvalidoError(ValidationError):
    """Días/Tareas Varias (carga manual, celdas `Lista!$J$6`/`$J$7` del Excel)
    no pueden ser negativos."""

    default_code: ClassVar[str] = "VALOR_INVALIDO"

    def __init__(self, campo: str, raw_value: int | float) -> None:
        super().__init__(f"{campo} inválido (no puede ser negativo): {raw_value!r}")


class CampoRequeridoError(ValidationError):
    """Campos de texto de una solicitud de TV (Razón Social/Sucursal/Tarea
    Realizada, columnas del Google Form que este flujo reemplaza) no pueden
    quedar vacíos."""

    default_code: ClassVar[str] = "CAMPO_REQUERIDO"

    def __init__(self, campo: str) -> None:
        super().__init__(f"{campo} es requerido")


class SolicitudTvNoEncontradaError(NotFoundError):
    default_code: ClassVar[str] = "SOLICITUD_TV_NO_ENCONTRADA"

    def __init__(self, solicitud_id: uuid.UUID) -> None:
        super().__init__(f"No existe la solicitud de TV {solicitud_id}")


class TecnicoNoVinculadoError(NotFoundError):
    """El usuario autenticado no tiene un `Empleado` de Gestión de Personal
    vinculado (`user_id`) con `siges_empresa_id` cargado — sin ese vínculo no
    hay forma de saber qué técnico de Siges es. Se resuelve desde Vacaciones
    → Gestión de Personal → Empleados (vincular el usuario y "Vincular con
    Siges")."""

    default_code: ClassVar[str] = "TECNICO_NO_VINCULADO"

    def __init__(self, user_id: uuid.UUID) -> None:
        super().__init__(
            f"Tu usuario ({user_id}) no está vinculado a un técnico de Siges — "
            "pedí que te vinculen desde Gestión de Personal."
        )
