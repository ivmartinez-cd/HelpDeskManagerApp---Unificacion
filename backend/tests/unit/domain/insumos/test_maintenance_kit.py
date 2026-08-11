"""Tests de la detección de kits de mantenimiento (van como Pre-Correctivo, no supply)."""

from src.modules.insumos.domain.services.maintenance_kit import is_maintenance_kit


def test_reorder_part_type_estructurado_es_lo_mas_confiable() -> None:
    assert is_maintenance_kit("", "MAINTENANCE_KIT")
    assert is_maintenance_kit("", "maintenance_kit")  # case-insensitive


def test_fallback_por_keywords_en_descripcion() -> None:
    assert is_maintenance_kit("HP LaserJet Fuser Kit 110V", "")
    assert is_maintenance_kit("Kit de mantenimiento 220V", "")


def test_toner_comun_no_es_kit() -> None:
    assert not is_maintenance_kit("Cartucho negro HP 414A", "")
    # 'FUSER' como type NO alcanza solo (fusores simples no-kit existen) — el legacy
    # recibía consumable_type y lo ignoraba a propósito.
    assert not is_maintenance_kit("Fuser 220V", "FUSER")
