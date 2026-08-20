from src.modules.liquidaciones.domain.services.geovalidacion_worklist import calcular_residuo


class TestCalcularResiduo:
    def test_certeza_absoluta_no_pasa_a_verificacion(self) -> None:
        hallazgos = [(1, "fuera_de_argentina"), (2, "latlon_invertidas")]
        residuo = calcular_residuo(hallazgos, confirmados_tier1b=set())
        assert residuo.certeza_absoluta == frozenset({1, 2})
        assert residuo.requiere_verificacion == frozenset()

    def test_sin_coordenadas_no_es_candidato_a_tier2(self) -> None:
        residuo = calcular_residuo([(1, "sin_coordenadas")], confirmados_tier1b=set())
        assert residuo.certeza_absoluta == frozenset()
        assert residuo.requiere_verificacion == frozenset()

    def test_pin_compartido_sin_confirmar_es_candidato(self) -> None:
        residuo = calcular_residuo([(1, "pin_compartido")], confirmados_tier1b=set())
        assert residuo.requiere_verificacion == frozenset({1})

    def test_confirmado_por_tier1b_no_es_candidato(self) -> None:
        residuo = calcular_residuo([(1, "pin_compartido")], confirmados_tier1b={1})
        assert residuo.requiere_verificacion == frozenset()

    def test_lejos_de_base_sin_confirmar_es_candidato(self) -> None:
        residuo = calcular_residuo([(1, "lejos_de_base")], confirmados_tier1b=set())
        assert residuo.requiere_verificacion == frozenset({1})

    def test_una_sucursal_con_multiples_hallazgos_cuenta_una_vez(self) -> None:
        hallazgos = [(1, "pin_compartido"), (1, "lejos_de_base")]
        residuo = calcular_residuo(hallazgos, confirmados_tier1b=set())
        assert residuo.requiere_verificacion == frozenset({1})

    def test_caso_real_san_juan_composicion(self) -> None:
        # Reproduce la medicion real 2026-08-19: 3 fuera_de_argentina + 1
        # latlon_invertidas (certeza), 301 pin_compartido + 4 lejos_de_base
        # sin confirmar (verificacion), resto confirmado por tier1b.
        hallazgos = (
            [(i, "fuera_de_argentina") for i in range(1, 4)]
            + [(4, "latlon_invertidas")]
            + [(100 + i, "pin_compartido") for i in range(432)]
            + [(600 + i, "lejos_de_base") for i in range(184)]
        )
        confirmados = {100 + i for i in range(131)} | {600 + i for i in range(61)}
        residuo = calcular_residuo(hallazgos, confirmados)
        assert residuo.certeza_absoluta == frozenset({1, 2, 3, 4})
        assert len(residuo.requiere_verificacion) == (432 - 131) + (184 - 61)
