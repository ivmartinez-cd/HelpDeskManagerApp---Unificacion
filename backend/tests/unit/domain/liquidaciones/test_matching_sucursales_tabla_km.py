"""Tests del matching N1/N2 de sucursales de Tabla KM ↔ Siges — casos reales
tomados de la medición SAN JUAN (Fase 0, 2026-08-19, 151 filas sin match)."""

import uuid

from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalCliente,
)
from src.modules.liquidaciones.domain.services.matching_sucursales_tabla_km import (
    FilaSinMatch,
    normalizar_nombre_fuerte,
    proponer_matches_tabla_km,
)


def _siges(id_: int, empresa: str, sucursal: str) -> SigesSucursalCliente:
    return SigesSucursalCliente(
        siges_sucursal_id=id_,
        empresa_nombre=empresa,
        sucursal_nombre=sucursal,
        domicilio=None,
        localidad=None,
        provincia=None,
    )


class TestNormalizarNombreFuerte:
    def test_caso_trampa_grado_vs_ordinal(self) -> None:
        # U+00B0 (signo de grado) vs U+00BA (ordinal masculino) — NFD (normalizar_nombre)
        # no los unifica, NFKD sí. Caso real confirmado en SAN JUAN.
        assert normalizar_nombre_fuerte("JINZ N°41 MANUEL LAINEZ") == normalizar_nombre_fuerte(
            "JINZ N.º 41 Manuel Lainez"
        )

    def test_sigla_con_puntos_eni(self) -> None:
        assert normalizar_nombre_fuerte("E.N.I. Nº 60") == normalizar_nombre_fuerte("ENI N.º 60")

    def test_sigla_con_puntos_eee(self) -> None:
        assert normalizar_nombre_fuerte("E.E.E. India Mariana") == normalizar_nombre_fuerte(
            "EEE India Mariana"
        )

    def test_abreviatura_provincia(self) -> None:
        assert normalizar_nombre_fuerte(
            "Escuela Provincia de la Pampa."
        ) == normalizar_nombre_fuerte("Escuela Pcia. de la Pampa")

    def test_abreviatura_provincial_y_prov(self) -> None:
        assert normalizar_nombre_fuerte("Escuela Provincial Chimbas I") == normalizar_nombre_fuerte(
            "Escuela Prov. Chimbas I"
        )

    def test_abreviatura_escuela(self) -> None:
        assert normalizar_nombre_fuerte("Esc. Mariano Necochea") == normalizar_nombre_fuerte(
            "Escuela Mariano Necochea"
        )

    def test_numero_nro(self) -> None:
        assert normalizar_nombre_fuerte("E.N.I. N 30 Elsa Bornemann") == normalizar_nombre_fuerte(
            "ENI Nro 30 Elsa Bornemann"
        )

    def test_numeros_distintos_no_igualan(self) -> None:
        assert normalizar_nombre_fuerte("JINZ Nº 4") != normalizar_nombre_fuerte("JINZ N.º 8")


class TestProponerMatchesTablaKm:
    def test_n1_auto_vinculable_por_simbolo(self) -> None:
        fila_id = uuid.uuid4()
        filas = [FilaSinMatch(fila_id, "Gobierno de San Juan", "JINZ N°41 MANUEL LAINEZ")]
        candidatos = [_siges(1, "Gobierno de San Juan", "JINZ N.º 41 Manuel Lainez")]

        propuestas = proponer_matches_tabla_km(filas, candidatos)

        assert len(propuestas[fila_id]) == 1
        candidato = propuestas[fila_id][0]
        assert candidato.siges_sucursal_id == 1
        assert candidato.nivel == "N1"
        assert candidato.score == 1.0

    def test_n2_con_confirmacion_variante_descriptiva(self) -> None:
        fila_id = uuid.uuid4()
        filas = [FilaSinMatch(fila_id, "Gobierno de San Juan", 'Escuela Marcos Sastre "Emer"')]
        candidatos = [_siges(2, "Gobierno de San Juan", "Escuela rural Marcos Sastre")]

        propuestas = proponer_matches_tabla_km(filas, candidatos)

        assert len(propuestas[fila_id]) == 1
        assert propuestas[fila_id][0].nivel == "N2"
        assert propuestas[fila_id][0].siges_sucursal_id == 2

    def test_numero_distinto_nunca_se_propone(self) -> None:
        # Ambas "JINZ", pero N.º 58 ≠ N.º 38 — sucursales distintas aunque el
        # texto alrededor del número se parezca (ratio ingenuo alto, real).
        fila_id = uuid.uuid4()
        filas = [FilaSinMatch(fila_id, "Gobierno de San Juan", "JINZ N.º 58 Cte. Espora")]
        candidatos = [_siges(3, "Gobierno de San Juan", "JINZ N.º 38 Ed. Popular")]

        propuestas = proponer_matches_tabla_km(filas, candidatos)

        assert fila_id not in propuestas

    def test_nombre_propio_distinto_nunca_auto_vincula(self) -> None:
        # Personas distintas con estructura de nombre parecida — ratio ingenuo
        # de secuencia da 0.85+ pero NO es la misma sucursal (falso positivo
        # real detectado en Fase 0.3). La garantía dura acá es que ESTO NUNCA
        # puede salir como N1 (auto-vinculable) — si aparece como sugerencia,
        # tiene que ser N2 (confirmación humana) con el motivo explicitando
        # qué nombre difiere, para que el operador lo descarte de un vistazo.
        fila_id = uuid.uuid4()
        filas = [FilaSinMatch(fila_id, "Gobierno de San Juan", "Escuela ANTONIO QUARANTA")]
        candidatos = [_siges(4, "Gobierno de San Juan", "Escuela Antonio Pulenta")]

        propuestas = proponer_matches_tabla_km(filas, candidatos)

        if fila_id in propuestas:
            candidato = propuestas[fila_id][0]
            assert candidato.nivel == "N2"
            assert "quaranta" in candidato.motivo and "pulenta" in candidato.motivo

    def test_ancla_por_empresa_no_cruza(self) -> None:
        # Misma "sucursal" genérica ('San Juan') pero empresas totalmente
        # distintas — caso real (Monte Verde S.A. / GENNEIA S.A.).
        fila_id = uuid.uuid4()
        filas = [FilaSinMatch(fila_id, "Monte Verde S.A.", "San Juan")]
        candidatos = [_siges(5, "GENNEIA S.A.", "San Juan")]

        propuestas = proponer_matches_tabla_km(filas, candidatos)

        assert fila_id not in propuestas

    def test_sin_candidatos_de_la_empresa_no_propone(self) -> None:
        fila_id = uuid.uuid4()
        filas = [FilaSinMatch(fila_id, "Natura", "Vanesa Caliz")]

        propuestas = proponer_matches_tabla_km(filas, [])

        assert propuestas == {}

    def test_top_n_limitado_y_rankeado(self) -> None:
        fila_id = uuid.uuid4()
        filas = [FilaSinMatch(fila_id, "Gobierno de San Juan", "Escuela Sec. Los Berros")]
        candidatos = [
            _siges(10, "Gobierno de San Juan", "Escuela Secundaria Los Berros"),
            _siges(11, "Gobierno de San Juan", "Escuela Secundaria de Zonda"),
            _siges(12, "Gobierno de San Juan", "Escuela Secundaria Tamberias"),
            _siges(13, "Gobierno de San Juan", "Escuela Secundaria Obispo Zapata"),
        ]

        propuestas = proponer_matches_tabla_km(filas, candidatos)

        assert propuestas[fila_id][0].siges_sucursal_id == 10
        assert propuestas[fila_id][0].nivel == "N1"
        assert len(propuestas[fila_id]) <= 3
