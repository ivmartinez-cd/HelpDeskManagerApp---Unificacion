"""Tests del pivot/planificación del sync de tarifarios (ADR-014, dataset 2)."""

from datetime import date

from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCostoServicio,
)
from src.modules.liquidaciones.domain.services.sync_tarifarios import (
    planificar_sync_tarifarios,
    proponer_mapeo_zonas,
)
from tests.unit.domain.liquidaciones.factories import make_tarifario


def _costo(
    descripcion: str = "Genérica",
    vigencia: date = date(2026, 7, 1),
    correctivo: float = 67820.0,
    **overrides: float,
) -> SigesCostoServicio:
    valores = {
        "preventivo": 31353.0,
        "instalacion": 67820.0,
        "pre_correctivo": 67820.0,
        "guardia": 90000.0,
        "sistemas": 67820.0,
        "costo_km": 758.96,
    }
    valores.update(overrides)
    return SigesCostoServicio(
        siges_empresa_id=137,
        descripcion=descripcion,
        vigencia_desde=vigencia,
        correctivo=correctivo,
        costo_km=valores["costo_km"],
        preventivo=valores["preventivo"],
        instalacion=valores["instalacion"],
        pre_correctivo=valores["pre_correctivo"],
        guardia=valores["guardia"],
        sistemas=valores["sistemas"],
    )


class TestPlanificar:
    def test_generica_pivotea_a_zona_none_y_crea_faltantes(self) -> None:
        plan = planificar_sync_tarifarios([], [_costo()], {})

        assert len(plan.a_crear) == 6  # los 6 tipos con costo > 0
        assert {c.zona for c in plan.a_crear} == {None}
        assert {c.vigencia_desde for c in plan.a_crear} == {date(2026, 7, 1)}
        correctivo = next(c for c in plan.a_crear if c.tipo_servicio == "correctivo")
        assert (correctivo.costo_servicio, correctivo.costo_km) == (67820.0, 758.96)

    def test_costo_cero_no_genera_candidata_pero_001_si(self) -> None:
        plan = planificar_sync_tarifarios([], [_costo(guardia=0.0, sistemas=0.01)], {})

        tipos = {c.tipo_servicio for c in plan.a_crear}
        assert "guardia" not in tipos
        assert "sistemas" in tipos  # el caso real Centro Cívico a $0,01

    def test_vigencia_existente_igual_es_sin_cambios(self) -> None:
        existente = make_tarifario(
            tipo_servicio="correctivo",
            zona=None,
            costo_servicio=67820.0,
            costo_km=758.96,
            vigencia_desde=date(2026, 7, 1),
        )
        costo = _costo(preventivo=0, instalacion=0, pre_correctivo=0, guardia=0, sistemas=0)

        plan = planificar_sync_tarifarios([existente], [costo], {})

        assert plan.a_crear == []
        assert plan.conflictos == []
        assert plan.sin_cambios == 1

    def test_vigencia_existente_con_costo_distinto_es_conflicto_no_escritura(self) -> None:
        existente = make_tarifario(
            tipo_servicio="correctivo",
            zona=None,
            costo_servicio=60000.0,
            costo_km=758.96,
            vigencia_desde=date(2026, 7, 1),
        )
        costo = _costo(preventivo=0, instalacion=0, pre_correctivo=0, guardia=0, sistemas=0)

        plan = planificar_sync_tarifarios([existente], [costo], {})

        assert plan.a_crear == []
        assert [(c.campo, c.valor_local, c.valor_siges) for c in plan.conflictos] == [
            ("costo_servicio", 60000.0, 67820.0)
        ]

    def test_descripcion_excluida_se_ignora(self) -> None:
        plan = planificar_sync_tarifarios([], [_costo(descripcion="DE BAJA")], {})

        assert plan.a_crear == []
        assert plan.zonas_sin_mapear == {}

    def test_descripcion_sin_mapeo_se_reporta_y_no_crea(self) -> None:
        plan = planificar_sync_tarifarios(
            [], [_costo(descripcion="Ushuaia - Infomac")] * 2, {}
        )

        assert plan.a_crear == []
        assert plan.zonas_sin_mapear == {"Ushuaia - Infomac": 2}

    def test_descripcion_mapeada_usa_la_zona_local(self) -> None:
        plan = planificar_sync_tarifarios(
            [], [_costo(descripcion="Ushuaia - Infomac")], {"Ushuaia - Infomac": "Ushuaia"}
        )

        assert {c.zona for c in plan.a_crear} == {"Ushuaia"}

    def test_descripcion_mapeada_a_generica_usa_zona_none(self) -> None:
        # El caso mayoritario real: la descripción es el código de tarifa del PST
        # ('TMTB122') y mapea explícitamente a la zona genérica.
        plan = planificar_sync_tarifarios(
            [], [_costo(descripcion="TMTB122")], {"TMTB122": None}
        )

        assert len(plan.a_crear) == 6
        assert {c.zona for c in plan.a_crear} == {None}
        assert plan.zonas_sin_mapear == {}


class TestProponerMapeoZonas:
    ZONAS_INFOMAC = [
        "Santiago del Estero",
        "Ushuaia",
        "Gral. Roca / Neuquén",
        "Buenos Aires",
        "Río Cuarto",
        "Villa Mercedes",
        "Rincon de los Sauces - Chos Malal - Barrancas - Buta Ranquil",
    ]

    def test_casos_reales_infomac(self) -> None:
        propuestas = proponer_mapeo_zonas(
            [
                "Ushuaia - Infomac",
                "Villa Mercedes / Rio IV /Sgo Estero /Bs.As.",
                "Rincon de los Sauces - Chos Malal - Barrancas - Buta Ranquil",
                "General Roca / Rio Negro / Neuquen / Cipoletti",
            ],
            self.ZONAS_INFOMAC,
        )

        assert propuestas == {
            "Ushuaia - Infomac": "Ushuaia",
            "Villa Mercedes / Rio IV /Sgo Estero /Bs.As.": "Villa Mercedes",
            "Rincon de los Sauces - Chos Malal - Barrancas - Buta Ranquil": (
                "Rincon de los Sauces - Chos Malal - Barrancas - Buta Ranquil"
            ),
            # 'General Roca...' no matchea 'Gral. Roca / Neuquén' — queda manual.
        }

    def test_ambiguedad_no_propone(self) -> None:
        propuestas = proponer_mapeo_zonas(["Zona Norte"], ["Norte", "Zona Norte GBA"])

        assert propuestas == {}
