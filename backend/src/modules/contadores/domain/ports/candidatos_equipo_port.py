from dataclasses import dataclass
from datetime import date
from typing import Protocol

from src.modules.contadores.domain.value_objects.tipo_toma import (
    ESTIMADO,
    PROMEDIO_INSTALACION,
    ST,
    es_inicial_final,
    es_real,
)

_WEB_CLIENTE = 18


@dataclass(frozen=True, slots=True)
class LecturaCandidataSiges:
    """Una lectura del panel de candidatos — `CandidatoContador` del legacy.
    `para_facturar` es `Tipo_Toma.Para_Facturar` (flag del tipo de toma, no
    de la fila de `Contadores`), como en `GetCandidatos.sql`. `id_empresa`/
    `id_sucursal`/`id_anexo` son el snapshot de ubicación de la lectura; las
    marcas `cambio_*_vs_anterior` comparan contra la lectura siguiente de la
    lista (la anterior en el tiempo) y son excluyentes: empresa > sucursal >
    anexo."""

    id_contador: int
    fecha: date
    tipo_toma: int
    valor: float
    para_facturar: bool
    desc_tipo_toma: str = ""
    id_empresa: int | None = None
    id_sucursal: int | None = None
    id_anexo: int | None = None
    cambio_empresa_vs_anterior: bool = False
    cambio_sucursal_vs_anterior: bool = False
    cambio_anexo_vs_anterior: bool = False

    @property
    def es_t4_st(self) -> bool:
        return self.tipo_toma == ST

    @property
    def es_estimado(self) -> bool:
        return self.tipo_toma in (ESTIMADO, PROMEDIO_INSTALACION)

    @property
    def es_web_cliente(self) -> bool:
        return self.tipo_toma == _WEB_CLIENTE

    @property
    def usable(self) -> bool:
        """`EsUsableComoCandidate`: real, T4 ST, inicial/final o web cliente
        — los estimados (T14/T19) y el resto no se ofrecen como P/L."""
        return (
            es_real(self.tipo_toma)
            or self.es_t4_st
            or es_inicial_final(self.tipo_toma)
            or self.es_web_cliente
        )

    @property
    def etiqueta_validacion(self) -> str:
        """`ValidacionLabel` del legacy, mismo orden de evaluación."""
        if self.es_estimado:
            return "⚠ est."
        if self.es_t4_st:
            return "⚠ T4" if self.para_facturar else "⚠ T4-PF0"
        if self.es_web_cliente:
            return "⚠ WC"
        if es_real(self.tipo_toma) or es_inicial_final(self.tipo_toma):
            return "✓ ok"
        return "—"


@dataclass(frozen=True, slots=True)
class MetadataEquipoSiges:
    nro_serie: str
    empresa: str
    sucursal: str
    sector: str | None
    modelo: str
    id_tecnologia: int
    velocidad: float | None


class CandidatosEquipoPort(Protocol):
    """Puerto de solo lectura contra Siges para el panel de candidatos
    manuales del Estimador (MODELO_DE_DATOS.md §3.6)."""

    async def fetch_lecturas(
        self, id_maquina: int, id_clase_contador: int
    ) -> list[LecturaCandidataSiges]:
        """Últimas 24 lecturas del equipo/clase, más recientes primero, con
        las marcas de cambio de empresa/sucursal/anexo ya calculadas."""
        ...

    async def fetch_lecturas_de_equipos(
        self, equipos: list[tuple[int, int]]
    ) -> dict[tuple[int, int], list[LecturaCandidataSiges]]:
        """Las mismas 24 lecturas de `fetch_lecturas` para varios
        (ID_Maquina, ID_ClaseContador) en una sola consulta, sin las marcas de
        cambio de ubicación. Un equipo sin lecturas no aparece."""
        ...

    async def fetch_metadata_equipo(self, id_maquina: int) -> MetadataEquipoSiges | None:
        """Identidad del equipo (ubicación y modelo actuales) — `None` si el
        `ID_Maquina` no existe en Siges."""
        ...
