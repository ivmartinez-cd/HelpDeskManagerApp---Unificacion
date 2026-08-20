"""Tests del matching N1/N2 de sucursales de Tabla KM ↔ Siges — casos reales
tomados de la medición SAN JUAN (Fase 0, 2026-08-19, 151 filas sin match)."""

import uuid

from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalCliente,
)
from src.modules.liquidaciones.domain.services.matching_sucursales_tabla_km import (
    FilaSinMatch,
    clave_direccion,
    normalizar_nombre_fuerte,
    proponer_matches_tabla_km,
)


def _siges(
    id_: int,
    empresa: str,
    sucursal: str,
    domicilio: str | None = None,
    localidad: str | None = None,
) -> SigesSucursalCliente:
    return SigesSucursalCliente(
        siges_sucursal_id=id_,
        empresa_nombre=empresa,
        sucursal_nombre=sucursal,
        domicilio=domicilio,
        localidad=localidad,
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


class TestClaveDireccion:
    def test_normaliza_sufijos_acentos_y_localidad(self) -> None:
        assert clave_direccion("Laprida e Independencia S/N 0", "San Juan") == clave_direccion(
            "LAPRIDA E INDEPENDENCIA s/n Piso: Dpto:", "SAN JUAN"
        )

    def test_direccion_generica_no_genera_clave(self) -> None:
        assert clave_direccion("S/N 0", "San Juan") is None
        assert clave_direccion(None, "San Juan") is None
        assert clave_direccion("0", None) is None

    def test_localidad_distinta_es_otra_clave(self) -> None:
        assert clave_direccion("San Martín 120", "Rawson") != clave_direccion(
            "San Martín 120", "Chimbas"
        )


class TestProponerPorDireccion:
    def test_renombrada_con_misma_direccion_se_propone_como_n2(self) -> None:
        # Caso real pedido por el usuario (2026-08-20): la escuela cambió de nombre en
        # Gestión pero conserva la dirección. Por nombre el score es ~0.
        fila_id = uuid.uuid4()
        filas = [
            FilaSinMatch(
                fila_id,
                "Gobierno de San Juan",
                "Escuela ANTONIO QUARANTA",
                "Laprida e Independencia S/N 0",
                "SAN JUAN",
            )
        ]
        candidatos = [
            _siges(
                7,
                "Gobierno de San Juan",
                "Escuela Mariano Ianelli",
                "Laprida e Independencia S/N 0",
                "San Juan",
            ),
            _siges(
                8, "Gobierno de San Juan", "Escuela Antonio Torres", "General Acha 426", "San Juan"
            ),
        ]

        propuestas = proponer_matches_tabla_km(filas, candidatos)

        top = propuestas[fila_id][0]
        assert top.siges_sucursal_id == 7
        assert top.nivel == "N2"
        assert top.misma_direccion is True
        assert top.motivo.startswith("misma dirección")

    def test_direccion_nunca_auto_vincula(self) -> None:
        fila_id = uuid.uuid4()
        filas = [
            FilaSinMatch(fila_id, "Natura", "Paola Rodriguez", "Bilibiscate 2658", "Córdoba")
        ]
        candidatos = [_siges(1, "Natura", "Romina Cerutti", "Bilibiscate 2658", "Córdoba")]

        propuestas = proponer_matches_tabla_km(filas, candidatos)

        assert all(c.nivel == "N2" for c in propuestas[fila_id])

    def test_n1_sigue_primero_aunque_otro_comparta_direccion(self) -> None:
        fila_id = uuid.uuid4()
        filas = [
            FilaSinMatch(fila_id, "Gobierno de San Juan", "E.N.I. Nº 60", "Mitre 100", "Rawson")
        ]
        candidatos = [
            _siges(1, "Gobierno de San Juan", "Escuela Albergue", "Mitre 100", "Rawson"),
            _siges(2, "Gobierno de San Juan", "ENI N.º 60", "Otra calle 5", "Rawson"),
        ]

        propuestas = proponer_matches_tabla_km(filas, candidatos)

        assert propuestas[fila_id][0].siges_sucursal_id == 2
        assert propuestas[fila_id][0].nivel == "N1"

    def test_numero_distinto_gana_a_la_direccion(self) -> None:
        fila_id = uuid.uuid4()
        filas = [
            FilaSinMatch(fila_id, "Gobierno de San Juan", "ENI N.º 4", "Mitre 100", "Rawson")
        ]
        candidatos = [_siges(1, "Gobierno de San Juan", "ENI N.º 8", "Mitre 100", "Rawson")]

        assert proponer_matches_tabla_km(filas, candidatos) == {}

    def test_direccion_generica_no_propone(self) -> None:
        fila_id = uuid.uuid4()
        # Nombres sin ningún parecido: solo la dirección podría proponerlos, y es genérica.
        filas = [
            FilaSinMatch(fila_id, "Gobierno de San Juan", "Escuela Uno", "S/N 0", "Rawson")
        ]
        candidatos = [
            _siges(1, "Gobierno de San Juan", "Jardin Maternal Arcoiris", "S/N 0", "Rawson")
        ]

        assert proponer_matches_tabla_km(filas, candidatos) == {}
