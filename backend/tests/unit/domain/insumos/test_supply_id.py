"""Tests del dígito verificador módulo-10 propio de Canal Directo."""

from src.modules.insumos.domain.value_objects.order_reference import order_reference
from src.modules.insumos.domain.value_objects.supply_id import ean_check_digit, supply_id_full


def test_check_digit_del_ejemplo_real_documentado() -> None:
    """"441415-9" es el formato real observado en getTopSupplies (ver caracterización)."""
    assert ean_check_digit(441415) == 9
    assert supply_id_full(441415) == "441415-9"


def test_check_digit_pesa_de_izquierda_a_derecha() -> None:
    """Acá "13" es 1*3 + 3*1 = 6 → (10-6)%10 = 4; con el EAN estándar (peso 3 desde el
    dígito más a la derecha) sería 1*1 + 3*3 = 10 → 0. El caso distingue ambos algoritmos."""
    assert ean_check_digit(13) == 4
    assert ean_check_digit("13") == 4


def test_order_reference_usa_prefijo_sds() -> None:
    assert order_reference(974325) == "SDS-974325"
