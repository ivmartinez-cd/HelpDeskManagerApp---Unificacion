"""DTO de salida de ImportarPrestadorMaestro."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ImportarPrestadorMaestroResultado:
    """`hoja_tabla_km=None` si el archivo no tenía ninguna hoja compatible con
    Tabla KM — sin esto la UI no puede distinguir esa situación de "la hoja
    estaba pero las filas ya existían"."""

    prestador_id: UUID
    prestador_creado: bool
    spsts_creados: int
    tarifarios_creados: int
    tarifarios_omitidos: int
    tabla_km_creadas: int
    tabla_km_omitidas: int
    hoja_tabla_km: str | None
