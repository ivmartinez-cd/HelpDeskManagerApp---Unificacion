"""Fake del puerto PrestadorMaestroFileParser — separado de `fakes.py` (ya en 366
líneas, sobre el límite de ARCHITECTURE_GUIDE §4) en vez de seguir agrandándolo."""

from src.modules.liquidaciones.domain.value_objects.prestador_maestro_importado import (
    ResultadoImportacionMaestro,
)


class FakePrestadorMaestroFileParser:
    """Devuelve un `ResultadoImportacionMaestro` fijo sin pasar por pandas."""

    def __init__(self, resultado: ResultadoImportacionMaestro) -> None:
        self.resultado = resultado
        self.calls: list[tuple[bytes, str]] = []

    def parse(self, contenido: bytes, nombre_archivo: str) -> ResultadoImportacionMaestro:
        self.calls.append((contenido, nombre_archivo))
        return self.resultado
