from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class RecesoCliente:
    """Período sin uso declarado para un cliente (`Receso` del legacy). Con
    `id_anexo` cargado aplica solo a ese anexo, sin mirar el grupo; sin anexo
    aplica a todo el grupo económico — ver `recesos_aplicables`."""

    fecha_desde: date
    fecha_hasta: date
    id_grupo_economico: int
    id_anexo: int | None
