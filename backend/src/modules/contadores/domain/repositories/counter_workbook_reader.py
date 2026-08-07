from typing import Protocol

from src.modules.contadores.domain.value_objects.device_readings import DeviceReadings


class CounterWorkbookReader(Protocol):
    """Puerto: parsea el Excel de lecturas de contadores a `DeviceReadings`
    agrupadas por (serie, clase). La implementación concreta (pandas/openpyxl)
    vive en infrastructure — el dominio no sabe que existe un Excel."""

    def read(self, file_path: str) -> list[DeviceReadings]: ...
