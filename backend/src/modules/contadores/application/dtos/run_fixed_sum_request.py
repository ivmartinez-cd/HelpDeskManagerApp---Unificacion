from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RunFixedSumRequest:
    file_paths: list[str]
    fecha: str
    hojas_a_sumar: int
    output_dir: str
