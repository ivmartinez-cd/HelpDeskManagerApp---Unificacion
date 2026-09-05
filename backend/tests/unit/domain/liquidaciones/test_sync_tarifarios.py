"""Tests del pivot/planificación del sync de tarifarios (ADR-014, dataset 2)."""

import uuid
from datetime import date

from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCostoServicio,
)
from src.modules.liquidaciones.domain.services.sync_tarifarios import (
    planificar_sync_tarifarios,
    proponer_mapeo_spst,
)
from tests.unit.domain.liquidaciones.factories import make_spst, make_tarifario


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
    def test_generica_pivotea_a_spst_none_y_crea_faltantes(self) -> None:
        plan = planificar_sync_tarifarios([], [_costo()], {})

        assert len(plan.a_crear) == 6  # los 6 tipos con costo > 0
        assert {c.spst_id for c in plan.a_crear} == {None}
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
            spst_id=None,
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
            spst_id=None,
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
        assert plan.sin_mapear == {}

    def test_descripcion_sin_mapeo_se_reporta_y_no_crea(self) -> None:
        plan = planificar_sync_tarifarios(
            [], [_costo(descripcion="Ushuaia - Infomac")] * 2, {}
        )

        assert plan.a_crear == []
        assert plan.sin_mapear == {"Ushuaia - Infomac": 2}

    def test_descripcion_mapeada_usa_el_spst_local(self) -> None:
        spst_id = uuid.uuid4()
        plan = planificar_sync_tarifarios(
            [], [_costo(descripcion="Ushuaia - Infomac")], {"Ushuaia - Infomac": spst_id}
        )

        assert {c.spst_id for c in plan.a_crear} == {spst_id}

    def test_descripcion_mapeada_a_generica_usa_spst_none(self) -> None:
        # El caso mayoritario real: la descripción es el código de tarifa del PST
        # ('TMTB122') y mapea explícitamente a la tarifa genérica.
        plan = planificar_sync_tarifarios(
            [], [_costo(descripcion="TMTB122")], {"TMTB122": None}
        )

        assert len(plan.a_crear) == 6
        assert {c.spst_id for c in plan.a_crear} == {None}
        assert plan.sin_mapear == {}


class TestProponerMapeoSpst:
    def test_casos_reales_infomac(self) -> None:
        spsts = [
            make_spst(nombre="Santiago del Estero"),
            make_spst(nombre="Ushuaia"),
            make_spst(nombre="Gral. Roca / Neuquén"),
            make_spst(nombre="Buenos Aires"),
            make_spst(nombre="Río Cuarto"),
            make_spst(nombre="Villa Mercedes"),
            make_spst(nombre="Rincon de los Sauces - Chos Malal - Barrancas - Buta Ranquil"),
        ]
        por_nombre = {s.nombre: s.id for s in spsts}

        propuestas = proponer_mapeo_spst(
            [
                "Ushuaia - Infomac",
                "Villa Mercedes / Rio IV /Sgo Estero /Bs.As.",
                "Rincon de los Sauces - Chos Malal - Barrancas - Buta Ranquil",
                "General Roca / Rio Negro / Neuquen / Cipoletti",
            ],
            spsts,
        )

        assert propuestas == {
            "Ushuaia - Infomac": por_nombre["Ushuaia"],
            "Villa Mercedes / Rio IV /Sgo Estero /Bs.As.": por_nombre["Villa Mercedes"],
            "Rincon de los Sauces - Chos Malal - Barrancas - Buta Ranquil": por_nombre[
                "Rincon de los Sauces - Chos Malal - Barrancas - Buta Ranquil"
            ],
            # 'General Roca...' no matchea 'Gral. Roca / Neuquén' — queda manual.
        }

    def test_ambiguedad_no_propone(self) -> None:
        spsts = [make_spst(nombre="Norte"), make_spst(nombre="Zona Norte GBA")]
        propuestas = proponer_mapeo_spst(["Zona Norte"], spsts)

        assert propuestas == {}

    def test_matchea_tambien_por_zona_cobertura(self) -> None:
        spst = make_spst(nombre="SPST 12", zona_cobertura="Ushuaia")
        propuestas = proponer_mapeo_spst(["Ushuaia - Infomac"], [spst])

        assert propuestas == {"Ushuaia - Infomac": spst.id}
