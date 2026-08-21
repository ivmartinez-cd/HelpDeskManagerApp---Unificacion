import pytest

from src.modules.auth.domain.errors import InvalidRoutePathError
from src.modules.auth.domain.value_objects.route_path import RoutePath


@pytest.mark.parametrize(
    "raw",
    [
        "/sla/pendientes-a-cerrar",
        "/insumos",
        "/liquidaciones/configuracion/tabla-km",
        "/contadores/anexos-pendientes",
    ],
)
def test_accepts_well_formed_routes(raw: str) -> None:
    assert RoutePath(raw).value == raw


def test_normalizes_case_and_trailing_slash() -> None:
    assert RoutePath("/Insumos/").value == "/insumos"


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "/",
        "insumos",
        "/liquidaciones/550e8400-e29b-41d4-a716-446655440000",  # id de detalle (UUID)
        "/liquidaciones/42",  # id de detalle (numérico)
        "javascript:alert(1)",
        "//evil.com",
        "/insumos?x=1",
        "/../../etc/passwd",
        "/a/b/c/d/e",  # más de 4 segmentos
        "/" + "a" * 130,  # excede el largo máximo
    ],
)
def test_rejects_malformed_routes(raw: str) -> None:
    with pytest.raises(InvalidRoutePathError):
        RoutePath(raw)


def test_module_key_is_the_first_segment() -> None:
    assert RoutePath("/sla/pendientes-a-cerrar").module_key == "sla"
