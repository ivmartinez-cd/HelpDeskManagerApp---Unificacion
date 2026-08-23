from src.modules.preventivos.domain.entities.sucursal_coordenadas import SucursalParaGeocoding
from src.modules.preventivos.domain.services.pines_sospechosos import (
    detectar_domicilios_en_conflicto,
    detectar_pines_compartidos,
)


def _sucursal(id_sucursal: int, domicilio: str, lat: float | None, lon: float | None):
    return SucursalParaGeocoding(
        id_sucursal=id_sucursal,
        cliente="Cliente",
        sucursal="Sucursal",
        domicilio=domicilio,
        ciudad="Ciudad",
        provincia="Provincia",
        latitud=lat,
        longitud=lon,
    )


def test_domicilios_distintos_con_mismo_pin_quedan_marcados() -> None:
    sucursales = [
        _sucursal(1, "Calle Falsa 123", -34.6, -58.4),
        _sucursal(2, "Otra Calle 456", -34.6, -58.4),
    ]
    assert detectar_pines_compartidos(sucursales) == {1, 2}


def test_mismo_domicilio_con_mismo_pin_no_se_marca() -> None:
    sucursales = [
        _sucursal(1, "Calle Falsa 123", -34.6, -58.4),
        _sucursal(2, "Calle Falsa 123", -34.6, -58.4),
    ]
    assert detectar_pines_compartidos(sucursales) == set()


def test_pin_unico_no_se_marca() -> None:
    sucursales = [_sucursal(1, "Calle Falsa 123", -34.6, -58.4)]
    assert detectar_pines_compartidos(sucursales) == set()


def test_coordenadas_cercanas_pero_no_identicas_no_se_marcan() -> None:
    sucursales = [
        _sucursal(1, "Calle Falsa 123", -34.60001, -58.40001),
        _sucursal(2, "Otra Calle 456", -34.60002, -58.40002),
    ]
    assert detectar_pines_compartidos(sucursales) == set()


def test_sin_coordenada_no_rompe() -> None:
    sucursales = [
        _sucursal(1, "Calle Falsa 123", None, None),
        _sucursal(2, "Otra Calle 456", -34.6, -58.4),
    ]
    assert detectar_pines_compartidos(sucursales) == set()


def test_grupo_de_mas_de_dos_con_un_domicilio_distinto_marca_todo_el_grupo() -> None:
    sucursales = [
        _sucursal(1, "Calle A", -34.6, -58.4),
        _sucursal(2, "Calle A", -34.6, -58.4),
        _sucursal(3, "Calle B", -34.6, -58.4),
    ]
    assert detectar_pines_compartidos(sucursales) == {1, 2, 3}


# --- detectar_domicilios_en_conflicto -----------------------------------


def test_mismo_domicilio_con_pines_lejanos_queda_marcado() -> None:
    # Caso real: "Av. Constituyentes 6020" con tres locales a ~1.5km entre sí.
    sucursales = [
        _sucursal(1, "Av. Constituyentes 6020", -34.5726, -58.5060),
        _sucursal(2, "Av. Constituyentes 6020", -34.5623, -58.5158),
    ]
    assert detectar_domicilios_en_conflicto(sucursales) == {1, 2}


def test_mismo_domicilio_con_pines_cercanos_no_se_marca() -> None:
    sucursales = [
        _sucursal(1, "Av. Constituyentes 6020", -34.5726, -58.5060),
        _sucursal(2, "Av. Constituyentes 6020", -34.57261, -58.50601),
    ]
    assert detectar_domicilios_en_conflicto(sucursales) == set()


def test_domicilio_distinto_no_se_compara() -> None:
    sucursales = [
        _sucursal(1, "Av. Constituyentes 6020", -34.5726, -58.5060),
        _sucursal(2, "Otra Calle 999", -31.5, -68.5),
    ]
    assert detectar_domicilios_en_conflicto(sucursales) == set()


def test_domicilio_en_conflicto_sin_coordenada_no_rompe() -> None:
    sucursales = [
        _sucursal(1, "Av. Constituyentes 6020", None, None),
        _sucursal(2, "Av. Constituyentes 6020", -34.5623, -58.5158),
    ]
    assert detectar_domicilios_en_conflicto(sucursales) == set()
