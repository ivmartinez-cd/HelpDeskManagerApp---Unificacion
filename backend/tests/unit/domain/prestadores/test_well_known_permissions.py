"""Los permisos well-known de prestadores están sembrados en la DB por su clave
(ADR-005) — un typo acá rompe la autorización en silencio, por eso se fijan."""

from src.modules.prestadores.domain import well_known_permissions as wkp


def test_las_claves_de_permisos_son_las_sembradas_en_db() -> None:
    assert wkp.VIEW.module.value == "prestadores"
    assert {p.action.value for p in (wkp.VIEW, wkp.CREATE, wkp.UPDATE, wkp.DELETE)} == {
        "view",
        "create",
        "update",
        "delete",
    }
