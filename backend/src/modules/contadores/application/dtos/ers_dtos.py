from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ErsClientResult:
    """Cliente ERS (grupo) combinado con su preferencia suma_color guardada."""

    id: str
    name: str
    suma_color: bool = False


@dataclass(frozen=True, slots=True)
class ExportErsMetersRequest:
    """Parámetros para exportar contadores de un grupo ERS a CSV."""

    group_id: str
    group_name: str
    max_date: str
    output_dir: str


@dataclass(frozen=True, slots=True)
class ExportErsMetersResult:
    """Resultado del proceso de exportación ERS."""

    csv_path: str
    filename: str
    group_name: str
