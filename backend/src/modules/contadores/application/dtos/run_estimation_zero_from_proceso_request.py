from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RunEstimationZeroFromProcesoRequest:
    nro_proceso: int
    fecha_nueva: str
    output_dir: str
