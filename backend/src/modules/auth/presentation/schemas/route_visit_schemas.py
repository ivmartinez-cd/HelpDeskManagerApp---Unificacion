from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from src.modules.auth.domain.entities.route_visit_count import RouteVisitCount


class RecordRouteVisitRequest(BaseModel):
    """Solo tipo y tamaño acá -- la gramática real de la ruta vive en el VO
    de dominio `RoutePath` (ADR-028), para que valga también fuera de HTTP."""

    model_config = ConfigDict(extra="forbid")

    route: str = Field(min_length=2, max_length=128)


class RouteVisitResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    route: str
    module_key: str = Field(serialization_alias="moduleKey")
    visits: int
    last_visit: date = Field(serialization_alias="lastVisit")

    @classmethod
    def from_domain(cls, entry: RouteVisitCount) -> "RouteVisitResponse":
        return cls(
            route=entry.route,
            module_key=entry.route[1:].split("/", 1)[0],
            visits=entry.visits,
            last_visit=entry.last_visit,
        )
