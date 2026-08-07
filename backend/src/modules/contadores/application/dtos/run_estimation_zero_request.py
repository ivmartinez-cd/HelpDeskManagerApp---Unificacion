from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RunEstimationZeroRequest:
    file_path: str
    cliente: str
    fecha_nueva: str
    output_dir: str
