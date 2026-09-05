from typing import Protocol

from src.modules.contadores.application.dtos.receso_dto import RecesoDto


class RecesosPort(Protocol):
    """Calendario de recesos de clientes (REGLAS_DE_NEGOCIO §6, MODELO_DE_DATOS
    §5) — dato propio de la app, CRUD completo. `RecesosEjemploStore` (en
    memoria, modo ejemplo) y `SqlAlchemyRecesosRepository` (Postgres, modo
    real) implementan este mismo shape sin heredar de él (Protocol
    estructural) — dos implementaciones separadas, no una compartida, para
    no mezclar IDs de ejemplo con IDs reales de grupo económico de Siges en
    la misma tabla."""

    async def listar(self, id_grupo_economico: int) -> list[RecesoDto]: ...
    async def crear(self, receso_sin_id: RecesoDto) -> RecesoDto: ...
    async def eliminar(self, id_receso: int) -> None: ...
