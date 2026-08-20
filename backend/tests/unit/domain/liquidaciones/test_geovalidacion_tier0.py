"""Tests de Tier 0 de geovalidación (Fase 2): saneo puro, sin llamadas."""

from src.modules.liquidaciones.domain.services.geovalidacion_tier0 import (
    SucursalParaValidar,
    evaluar_tier0,
)

# San Juan capital real, usado como referencia de "dentro de Argentina".
_LAT_SJ, _LON_SJ = -31.5375, -68.5364


def _sucursal(
    id_: int,
    *,
    lat: float | None = _LAT_SJ,
    lon: float | None = _LON_SJ,
    domicilio: str | None = "Mitre 123",
    provincia: str | None = "San Juan",
) -> SucursalParaValidar:
    return SucursalParaValidar(
        siges_sucursal_id=id_,
        empresa_nombre="Empresa",
        sucursal_nombre=f"Sucursal {id_}",
        domicilio=domicilio,
        provincia=provincia,
        latitud=lat,
        longitud=lon,
    )


class TestEvaluarTier0:
    def test_sucursal_limpia_no_genera_hallazgos(self) -> None:
        assert evaluar_tier0([_sucursal(1)]) == []

    def test_sin_coordenadas(self) -> None:
        hallazgos = evaluar_tier0([_sucursal(1, lat=None, lon=None)])
        assert len(hallazgos) == 1
        assert hallazgos[0].codigo == "sin_coordenadas"
        assert hallazgos[0].severidad == "baja"

    def test_pin_en_cero_cero(self) -> None:
        hallazgos = evaluar_tier0([_sucursal(1, lat=0.0, lon=0.0)])
        assert hallazgos[0].codigo == "sin_coordenadas"

    def test_fuera_de_argentina(self) -> None:
        # Brasilia aprox — claramente fuera del rectángulo.
        hallazgos = evaluar_tier0([_sucursal(1, lat=-15.79, lon=-47.88)])
        assert len(hallazgos) == 1
        assert hallazgos[0].codigo == "fuera_de_argentina"
        assert hallazgos[0].severidad == "alta"

    def test_latlon_invertidas(self) -> None:
        # Alguien cargó (lon, lat) en vez de (lat, lon): el par tal cual está
        # fuera de Argentina, invertido cae exacto en San Juan.
        hallazgos = evaluar_tier0([_sucursal(1, lat=_LON_SJ, lon=_LAT_SJ)])
        assert len(hallazgos) == 1
        assert hallazgos[0].codigo == "latlon_invertidas"
        assert hallazgos[0].severidad == "alta"

    def test_pin_compartido_con_domicilio_distinto(self) -> None:
        sucursales = [
            _sucursal(1, domicilio="Mitre 123"),
            _sucursal(2, domicilio="Rivadavia 456"),
        ]
        hallazgos = evaluar_tier0(sucursales)
        codigos = {h.codigo for h in hallazgos}
        assert codigos == {"pin_compartido"}
        assert {h.siges_sucursal_id for h in hallazgos} == {1, 2}

    def test_pin_compartido_mismo_domicilio_no_alerta(self) -> None:
        # Mismo edificio, mismo domicilio — no es "todas al centro".
        sucursales = [
            _sucursal(1, domicilio="Mitre 123"),
            _sucursal(2, domicilio="Mitre 123"),
        ]
        assert evaluar_tier0(sucursales) == []

    def test_pin_unico_no_alerta_aunque_domicilio_distinto(self) -> None:
        sucursales = [_sucursal(1, domicilio="Mitre 123")]
        assert evaluar_tier0(sucursales) == []

    def test_lejos_de_base(self) -> None:
        base = (_LAT_SJ, _LON_SJ)
        lejos = _sucursal(1, lat=-38.0, lon=-57.5)  # Mar del Plata, ~700 km
        hallazgos = evaluar_tier0([lejos], base=base, umbral_distancia_base_km=300.0)
        assert len(hallazgos) == 1
        assert hallazgos[0].codigo == "lejos_de_base"
        assert hallazgos[0].severidad == "media"

    def test_cerca_de_base_no_alerta(self) -> None:
        base = (_LAT_SJ, _LON_SJ)
        cerca = _sucursal(1, lat=_LAT_SJ + 0.05, lon=_LON_SJ + 0.05)
        assert evaluar_tier0([cerca], base=base, umbral_distancia_base_km=300.0) == []

    def test_sin_base_no_evalua_distancia(self) -> None:
        lejos = _sucursal(1, lat=-38.0, lon=-57.5)
        assert evaluar_tier0([lejos], base=None) == []

    def test_umbral_default_calibrado_con_san_juan(self) -> None:
        # Calibración real 2026-08-19: hueco natural sin ninguna sucursal
        # entre 284 km (la más lejana real, dentro de la provincia) y 402 km
        # (la más cercana entre las que ya tienen pin roto confirmado en
        # otra provincia) — 350 (el default) cae justo en el medio.
        base = (_LAT_SJ, _LON_SJ)
        dentro_del_hueco = _sucursal(1, lat=-34.6, lon=-68.5)  # ~314 km
        hallazgos = evaluar_tier0([dentro_del_hueco], base=base)
        assert hallazgos == []

    def test_una_sucursal_puede_tener_mas_de_un_hallazgo(self) -> None:
        base = (_LAT_SJ, _LON_SJ)
        # Fuera de Argentina Y lejos de la base.
        sucursal = _sucursal(1, lat=-15.79, lon=-47.88)
        hallazgos = evaluar_tier0([sucursal], base=base, umbral_distancia_base_km=300.0)
        codigos = {h.codigo for h in hallazgos}
        assert codigos == {"fuera_de_argentina", "lejos_de_base"}
