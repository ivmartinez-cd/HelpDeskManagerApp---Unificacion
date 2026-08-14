"""Equipo del parque que sigue facturando pero sin contador real reciente.

Réplica del dominio del reporte legacy `Operaciones/EquiposSinContadorReal`
de sitesphp, validada con paridad exacta contra Siges (2026-08-14): "toma
real" es cualquier `ID_TipoToma` fuera de {8 Contador Inicial, 13 Contador
Final, 14 Estimado, 19 Promedio Instalación}; si el equipo nunca tuvo una
real, la referencia es su primera toma histórica (fecha de instalación).
"""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class EquipoSinReal:
    # ID de Maquina en Siges — la serie no alcanza como identidad (hay series
    # sucias/duplicadas en el legacy, ej. '68H5101!mal').
    id_maquina: int
    # ID_Empresa del cliente en Siges — permite cruzar contra el calendario
    # de Gestión (operador asignado) sin re-matchear por nombre.
    id_empresa_cliente: int
    serie: str
    modelo: str
    tecnologia: str | None
    propiedad: str | None
    cliente: str
    sucursal: str
    estado_maquina: str
    observaciones: str
    # None = nunca tuvo una toma real; `fecha_referencia` pasa a ser la
    # primera toma histórica (instalación), igual que el legacy.
    fecha_ultimo_real: date | None
    fecha_referencia: date
    dias_sin_real: int
    meses_sin_real: int
    # Impresiones (mono+color) de los últimos 3 períodos entre tomas
    # consecutivas, de la más reciente hacia atrás.
    im1: int
    im2: int
    im3: int

    @property
    def nunca_tuvo_real(self) -> bool:
        return self.fecha_ultimo_real is None

    @property
    def imp_prom_3m(self) -> int:
        # Truncado, no redondeado: el legacy muestra 472 para (194+232+992)/3.
        return (self.im1 + self.im2 + self.im3) // 3


@dataclass(frozen=True)
class EquiposSinRealSnapshot:
    """Resultado de una consulta al parque con su marca de tiempo — la
    consulta es cara (~10s contra MERCURIO) y se sirve cacheada, así que la
    UI necesita saber de cuándo son los datos."""

    equipos: list[EquipoSinReal]
    consultado_en: datetime
