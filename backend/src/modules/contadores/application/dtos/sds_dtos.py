from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SdsClientResult:
    """Cliente SDS combinado con su preferencia suma_color guardada."""

    id: str
    name: str
    suma_color: bool = False


@dataclass(frozen=True, slots=True)
class ExportSdsMetersRequest:
    """Parámetros para exportar contadores SDS a CSV."""

    customer_id: str
    customer_name: str
    max_date: str
    output_dir: str


@dataclass(frozen=True, slots=True)
class ExportSdsMetersResult:
    """Resultado del proceso de exportación de contadores SDS."""

    csv_path: str
    filename: str
    customer_name: str
