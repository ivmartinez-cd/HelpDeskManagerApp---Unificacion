from src.modules.preventivos.domain.services.zonas import zona_excluida

_PATRONES = (
    "INTERIOR",
    "A DEFINIR",
    "PROPIO",
    "KIKO",
    "0000000000",
    "BSAS.*",
    "CBA..*",
    "CUYO.*",
    "NOA..*",
    "COSTA*",
)


def test_zonas_locales_no_se_excluyen() -> None:
    for zona in ("SUR", "SUROESTE", "CABA", "CABA-N", "NORTE1", "OESTE", "CENTRO", "SMARTIN"):
        assert not zona_excluida(zona, _PATRONES)


def test_exclusion_exacta() -> None:
    assert zona_excluida("INTERIOR", _PATRONES)
    assert zona_excluida("A DEFINIR", _PATRONES)


def test_exclusion_por_prefijo() -> None:
    assert zona_excluida("BSAS.1", _PATRONES)
    assert zona_excluida("CBA..3", _PATRONES)
    assert zona_excluida("COSTA2", _PATRONES)


def test_zona_nueva_local_aparece_sin_tocar_config() -> None:
    # La lista es de exclusión: NORTE5 (si mañana existe) es visible sola.
    assert not zona_excluida("NORTE5", _PATRONES)


def test_zona_vacia_siempre_excluida() -> None:
    assert zona_excluida("", _PATRONES)
    assert zona_excluida("   ", ())


def test_comparacion_normalizada() -> None:
    assert zona_excluida(" interior ", _PATRONES)
    assert not zona_excluida(" sur ", _PATRONES)
