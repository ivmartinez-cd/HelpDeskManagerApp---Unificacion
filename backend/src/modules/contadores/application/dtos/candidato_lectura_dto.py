from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class CandidatoLecturaDto:
    """Una fila del panel de candidatos (`CandidatoContador` del legacy).

    `usable` habilita P/L (`EsUsableComoCandidate`); `etiqueta_validacion`
    es la columna "Valid." del legacy (`ValidacionLabel`). `valido`/
    `motivo_invalidez` se derivan de esa etiqueta para los clientes que
    todavía los leen: `valido` solo si la etiqueta es "✓ ok", y el motivo es
    la propia etiqueta. `para_facturar` es `Tipo_Toma.Para_Facturar`.
    `id_contador` identifica la lectura para restaurar una P/L manual.
    Los campos con default existen para el modo ejemplo, que no los tiene."""

    fecha: date
    tipo_toma: int
    valor: float
    valido: bool
    motivo_invalidez: str | None
    id_contador: int | None = None
    desc_tipo_toma: str = ""
    para_facturar: bool = True
    usable: bool = True
    etiqueta_validacion: str = ""
    cambio_empresa_vs_anterior: bool = False
    cambio_sucursal_vs_anterior: bool = False
    cambio_anexo_vs_anterior: bool = False
