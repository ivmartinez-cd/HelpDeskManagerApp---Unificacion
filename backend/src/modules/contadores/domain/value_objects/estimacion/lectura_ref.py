from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class LecturaRef:
    """Una lectura de contador citada como Partida, Llegada, T4 o último
    facturado — valor + fecha + tipo de toma SiGes. `para_facturar` solo
    importa para una Llegada T4 elegida a mano (`RecalcularConPL` del legacy
    marca `BordeAmarilloT4PFcero` con `EsT4ST && !Para_Facturar`); en el
    resto de los usos no se mira."""

    valor: float
    fecha: date
    tipo_toma: int
    para_facturar: bool = True
