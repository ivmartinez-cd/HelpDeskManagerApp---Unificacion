"""Tests de caracterización del motor de reglas — puerto de los 22 tests escritos
contra el legacy (`LIQUIDACION_PRESTADORES_CARACTERIZACION.md` §7), adaptados a la
versión de dominio pura (sin DB) de `ejecutar_motor_reglas`. Cada caso reproduce el
mismo escenario de negocio verificado contra el código legacy real."""

import uuid
from datetime import date

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.services.motor_reglas.motor import ejecutar_motor_reglas
from tests.unit.domain.liquidaciones.factories import (
    make_incidente,
    make_regla,
    make_tabla_km,
    make_tarifario,
    reglas_activas_default,
)


class TestAlt001PrecioIncorrecto:
    def test_no_dispara_cuando_coincide_con_tarifario(self) -> None:
        tarifario = make_tarifario(costo_servicio=1500.0)
        incidente = make_incidente(costo_servicio_cobrado=1500.0)
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [tarifario]
        )
        assert resultado.alertas == []
        assert resultado.incidentes_evaluados[0].costo_servicio_esperado == 1500.0

    def test_dispara_cuando_difiere_del_tarifario(self) -> None:
        tarifario = make_tarifario(costo_servicio=1500.0)
        incidente = make_incidente(costo_servicio_cobrado=1800.0)
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [tarifario]
        )
        alertas = [a for a in resultado.alertas if a.tipo_alerta == "ALT001"]
        assert len(alertas) == 1
        assert alertas[0].datos_contexto == {
            "cobrado": 1800.0,
            "esperado": 1500.0,
            "diferencia": 300.0,
            "tipo_servicio": "correctivo",
        }
        assert alertas[0].riesgo == 100.0

    def test_tolerancia_de_un_centavo_no_dispara(self) -> None:
        tarifario = make_tarifario(costo_servicio=1500.0)
        incidente = make_incidente(costo_servicio_cobrado=1500.01)
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [tarifario]
        )
        assert resultado.alertas == []


class TestAlt002KmsIncorrectos:
    def test_no_dispara_dentro_de_tolerancia(self) -> None:
        tabla = make_tabla_km(kms_a_facturar=100.0)
        incidente = make_incidente(
            empresa_nombre=tabla.empresa_nombre,
            sucursal_nombre=tabla.sucursal_nombre,
            cant_km_cobrado=100.3,
        )
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [tabla], []
        )
        # Sin tarifario en este escenario, ALT008 (Tarifario Inexistente) también
        # dispara — es correcto, no es lo que este test verifica.
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT002"] == []
        assert resultado.incidentes_evaluados[0].cant_km_esperado == 100.0

    def test_dispara_sin_ruta_compartida(self) -> None:
        tabla = make_tabla_km(kms_a_facturar=100.0)
        incidente = make_incidente(
            empresa_nombre=tabla.empresa_nombre,
            sucursal_nombre=tabla.sucursal_nombre,
            cant_km_cobrado=60.0,
        )
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [tabla], []
        )
        alertas = [a for a in resultado.alertas if a.tipo_alerta == "ALT002"]
        assert len(alertas) == 1
        assert alertas[0].datos_contexto["diferencia"] == 40.0

    def test_fila_sin_km_marca_sin_referencia_en_vez_de_km_incorrectos(self) -> None:
        tabla = make_tabla_km(kms_a_facturar=0.0)
        incidente = make_incidente(
            empresa_nombre=tabla.empresa_nombre,
            sucursal_nombre=tabla.sucursal_nombre,
            cant_km_cobrado=26.0,
        )
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [tabla], []
        )
        alertas = [a for a in resultado.alertas if a.tipo_alerta == "ALT002"]
        assert len(alertas) == 1
        assert alertas[0].datos_contexto["sin_referencia"] is True
        assert "no tiene km de referencia" in (alertas[0].descripcion or "")

    def test_cobro_cero_sin_corredor_lista_candidatos_de_ruta(self) -> None:
        tabla = make_tabla_km(kms_a_facturar=120.0, localidad_cliente="Santa Rosa")
        otra = make_tabla_km(
            prestador_id=tabla.prestador_id,
            empresa_nombre="OCA",
            sucursal_nombre="Central",
            kms_a_facturar=300.0,
            localidad_cliente="Cipolletti",
        )
        sin_km = make_incidente(
            empresa_nombre=tabla.empresa_nombre,
            sucursal_nombre=tabla.sucursal_nombre,
            cant_km_cobrado=0.0,
        )
        con_km = make_incidente(
            numero_incidente="777",
            empresa_nombre="OCA",
            sucursal_nombre="Central",
            cant_km_cobrado=300.0,
            fecha_cierre=sin_km.fecha_cierre,
        )
        resultado = ejecutar_motor_reglas(
            [sin_km, con_km], [sin_km, con_km], reglas_activas_default(), [tabla, otra], []
        )
        alerta = next(
            a
            for a in resultado.alertas
            if a.tipo_alerta == "ALT002" and a.incidente_id == sin_km.id
        )
        assert alerta.datos_contexto["posible_ruta_compartida"] is True
        assert alerta.datos_contexto["candidatos"][0]["numero_incidente"] == "777"
        assert "#777" in (alerta.descripcion or "")

    def test_kms_decimal_cobrado_ceil_no_dispara(self) -> None:
        """kms_a_facturar=20.5: el PST cobra 21 (ceil correcto). Con tolerancia
        estricta (0) no debe disparar porque ceil(20.5)=21=cobrado."""
        tabla = make_tabla_km(kms_a_facturar=20.5)
        incidente = make_incidente(
            empresa_nombre=tabla.empresa_nombre,
            sucursal_nombre=tabla.sucursal_nombre,
            cant_km_cobrado=21.0,
        )
        reglas = dict(reglas_activas_default())
        reglas["ALT002"] = make_regla(
            codigo="ALT002",
            riesgo_base=100.0,
            activa=True,
            configuracion={"tolerancia_km": 0.0},
        )
        resultado = ejecutar_motor_reglas([incidente], [incidente], reglas, [tabla], [])
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT002"] == []

    def test_kms_cobrado_piso_de_decimal_no_dispara(self) -> None:
        """H-4 (validación 2026-08-13): tabla 71.3, PST cobra 71 (el piso). Comparar
        solo contra ceil(71.3)=72 daba |71-72|=1 > 0.5 y disparaba — la tolerancia
        aplica también contra el valor crudo de la tabla (|71-71.3|=0.3 ≤ 0.5)."""
        tabla = make_tabla_km(kms_a_facturar=71.3)
        incidente = make_incidente(
            empresa_nombre=tabla.empresa_nombre,
            sucursal_nombre=tabla.sucursal_nombre,
            cant_km_cobrado=71.0,
        )
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [tabla], []
        )
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT002"] == []

    def test_kms_cobrado_decimal_exacto_no_dispara_con_tolerancia_cero(self) -> None:
        """Cobrar exactamente el decimal de la tabla nunca es alerta, ni con
        tolerancia 0 (antes del fix H-4, ceil lo convertía en diferencia 0.7)."""
        tabla = make_tabla_km(kms_a_facturar=20.3)
        incidente = make_incidente(
            empresa_nombre=tabla.empresa_nombre,
            sucursal_nombre=tabla.sucursal_nombre,
            cant_km_cobrado=20.3,
        )
        reglas = dict(reglas_activas_default())
        reglas["ALT002"] = make_regla(
            codigo="ALT002",
            riesgo_base=100.0,
            activa=True,
            configuracion={"tolerancia_km": 0.0},
        )
        resultado = ejecutar_motor_reglas([incidente], [incidente], reglas, [tabla], [])
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT002"] == []

    def test_ruta_compartida_suprime_falso_positivo(self) -> None:
        liquidacion_id = uuid.uuid4()
        fecha = date(2026, 1, 15)
        tabla_a = make_tabla_km(
            kms_a_facturar=50.0,
            localidad_cliente="Rafaela",
            empresa_nombre="E",
            sucursal_nombre="A",
        )
        tabla_b = make_tabla_km(
            kms_a_facturar=50.0,
            localidad_cliente="Rafaela",
            empresa_nombre="E",
            sucursal_nombre="B",
        )
        inc_a = make_incidente(
            liquidacion_id=liquidacion_id,
            empresa_nombre="E",
            sucursal_nombre="A",
            fecha_cierre=fecha,
            cant_km_cobrado=0.0,
        )
        inc_b = make_incidente(
            liquidacion_id=liquidacion_id,
            empresa_nombre="E",
            sucursal_nombre="B",
            fecha_cierre=fecha,
            cant_km_cobrado=90.0,
        )
        resultado = ejecutar_motor_reglas(
            [inc_a, inc_b], [inc_a, inc_b], reglas_activas_default(), [tabla_a, tabla_b], []
        )
        alertas = [a for a in resultado.alertas if a.tipo_alerta == "ALT002"]
        # inc_a (0 vs 50) se suprime por ruta compartida; inc_b (90 vs 50) dispara la suya.
        assert len(alertas) == 1
        assert alertas[0].incidente_id == inc_b.id


class TestAlt003ViaticoDuplicado:
    def test_no_dispara_con_fechas_distintas(self) -> None:
        inc1 = make_incidente(
            empresa_nombre="E", sucursal_nombre="S", fecha_cierre=date(2026, 1, 10)
        )
        inc2 = make_incidente(
            empresa_nombre="E", sucursal_nombre="S", fecha_cierre=date(2026, 1, 15)
        )
        todos = [inc1, inc2]
        resultado = ejecutar_motor_reglas(todos, todos, reglas_activas_default(), [], [])
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT003"] == []

    def test_dispara_alertas_mutuas_mismo_dia_y_sucursal(self) -> None:
        fecha = date(2026, 1, 15)
        inc1 = make_incidente(
            numero_incidente="1",
            empresa_nombre="E",
            sucursal_nombre="S",
            fecha_cierre=fecha,
            cant_km_cobrado=10.0,
        )
        inc2 = make_incidente(
            numero_incidente="2",
            empresa_nombre="E",
            sucursal_nombre="S",
            fecha_cierre=fecha,
            cant_km_cobrado=20.0,
        )
        todos = [inc1, inc2]
        resultado = ejecutar_motor_reglas(todos, todos, reglas_activas_default(), [], [])
        alertas = [a for a in resultado.alertas if a.tipo_alerta == "ALT003"]
        assert len(alertas) == 2
        assert {a.incidente_id for a in alertas} == {inc1.id, inc2.id}

    def test_ventana_dias_es_config_muerta(self) -> None:
        """`ventana_dias` en `configuracion` nunca se lee — dos incidentes a 5 días de
        distancia (dentro de la "ventana" de 30) siguen sin disparar, porque el
        evaluador compara `fecha_cierre` exacto."""
        inc1 = make_incidente(
            empresa_nombre="E", sucursal_nombre="S", fecha_cierre=date(2026, 1, 10)
        )
        inc2 = make_incidente(
            empresa_nombre="E", sucursal_nombre="S", fecha_cierre=date(2026, 1, 15)
        )
        todos = [inc1, inc2]
        reglas = reglas_activas_default()
        reglas["ALT003"] = make_regla(codigo="ALT003", configuracion={"ventana_dias": 30})
        resultado = ejecutar_motor_reglas(todos, todos, reglas, [], [])
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT003"] == []


class TestAlt004ServicioDuplicado:
    def test_no_dispara_con_numero_unico(self) -> None:
        incidente = make_incidente(numero_incidente="500")
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], []
        )
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT004"] == []

    def test_dispara_cuando_ya_fue_liquidado_antes(self) -> None:
        liq_previa = uuid.uuid4()
        inc_actual = make_incidente(numero_incidente="500")
        inc_previo = make_incidente(numero_incidente="500", liquidacion_id=liq_previa)
        resultado = ejecutar_motor_reglas(
            [inc_actual], [inc_actual, inc_previo], reglas_activas_default(), [], []
        )
        alertas = [a for a in resultado.alertas if a.tipo_alerta == "ALT004"]
        assert len(alertas) == 1
        assert alertas[0].datos_contexto["liquidaciones_previas"] == [str(liq_previa)]


class TestAlt010SerieDuplicada:
    def test_no_dispara_sin_serie(self) -> None:
        incidente = make_incidente(nro_serie=None, tipo="correctivo")
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], []
        )
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT010"] == []

    def test_no_dispara_mismo_tipo_misma_serie(self) -> None:
        fecha = date(2026, 1, 10)
        inc1 = make_incidente(nro_serie="SN-1", tipo="correctivo", fecha_cierre=fecha)
        inc2 = make_incidente(nro_serie="SN-1", tipo="correctivo", fecha_cierre=fecha)
        resultado = ejecutar_motor_reglas([inc1], [inc1, inc2], reglas_activas_default(), [], [])
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT010"] == []

    def test_no_dispara_misma_serie_distinto_periodo(self) -> None:
        preventivo = make_incidente(
            nro_serie="SN-1", tipo="preventivo", fecha_cierre=date(2026, 1, 5)
        )
        correctivo = make_incidente(
            nro_serie="SN-1", tipo="correctivo", fecha_cierre=date(2026, 2, 5)
        )
        resultado = ejecutar_motor_reglas(
            [correctivo], [preventivo, correctivo], reglas_activas_default(), [], []
        )
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT010"] == []

    def test_dispara_preventivo_y_correctivo_misma_serie_mismo_periodo(self) -> None:
        preventivo = make_incidente(
            numero_incidente="100",
            nro_serie="SN-1",
            tipo="preventivo",
            fecha_cierre=date(2026, 1, 5),
        )
        correctivo = make_incidente(
            numero_incidente="200",
            nro_serie="SN-1",
            tipo="correctivo",
            fecha_cierre=date(2026, 1, 20),
        )
        resultado = ejecutar_motor_reglas(
            [correctivo], [preventivo, correctivo], reglas_activas_default(), [], []
        )
        alertas = [a for a in resultado.alertas if a.tipo_alerta == "ALT010"]
        assert len(alertas) == 1
        assert alertas[0].datos_contexto["nro_serie"] == "SN-1"
        assert alertas[0].datos_contexto["incidentes_relacionados"] == ["100"]
        assert alertas[0].datos_contexto["serie_duplicada"] is True
        assert alertas[0].riesgo == 90.0


class TestAlt005RutaCompartida:
    def _escenario_corredor(
        self,
    ) -> tuple[list[Incidente], list[TablaKm]]:
        liquidacion_id = uuid.uuid4()
        fecha = date(2026, 1, 15)
        tabla1 = make_tabla_km(
            localidad_cliente="Rafaela",
            kms_recorrido=90.0,
            empresa_nombre="E",
            sucursal_nombre="S1",
        )
        tabla2 = make_tabla_km(
            localidad_cliente="Rafaela",
            kms_recorrido=90.0,
            empresa_nombre="E",
            sucursal_nombre="S2",
        )
        inc1 = make_incidente(
            liquidacion_id=liquidacion_id,
            empresa_nombre="E",
            sucursal_nombre="S1",
            fecha_cierre=fecha,
            cant_km_cobrado=90.0,
            costo_total_cobrado=1000.0,
        )
        inc2 = make_incidente(
            liquidacion_id=liquidacion_id,
            empresa_nombre="E",
            sucursal_nombre="S2",
            fecha_cierre=fecha,
            cant_km_cobrado=90.0,
            costo_total_cobrado=1100.0,
        )
        return [inc1, inc2], [tabla1, tabla2]

    def test_un_solo_incidente_no_genera_alerta_grupo(self) -> None:
        tabla = make_tabla_km(localidad_cliente="Rafaela")
        incidente = make_incidente(
            empresa_nombre=tabla.empresa_nombre,
            sucursal_nombre=tabla.sucursal_nombre,
            cant_km_cobrado=50.0,
        )
        reglas = reglas_activas_default()
        reglas["ALT005"] = make_regla(codigo="ALT005", activa=True)
        resultado = ejecutar_motor_reglas([incidente], [incidente], reglas, [tabla], [])
        assert [a for a in resultado.alertas if a.es_grupo] == []

    def test_grupo_activo_genera_alerta_grupo_critica(self) -> None:
        incidentes, tablas = self._escenario_corredor()
        reglas = reglas_activas_default()
        reglas["ALT005"] = make_regla(codigo="ALT005", activa=True)
        resultado = ejecutar_motor_reglas(incidentes, incidentes, reglas, tablas, [])
        grupos = [a for a in resultado.alertas if a.es_grupo]
        assert len(grupos) == 1
        alerta = grupos[0]
        assert alerta.tipo_alerta == "ALT005"
        assert alerta.riesgo == 90.0  # CRITICO
        assert set(alerta.grupo_incidente_ids) == {i.id for i in incidentes}

    def test_genera_observaciones_false_apaga_solo_el_camino_agrupado(self) -> None:
        """Segundo switch (auditoría: "un switch controla dos comportamientos en
        ALT005") — con `activa=True` pero `genera_observaciones=False`, la Alerta
        por-incidente sigue disparando, la alerta agrupada no."""
        incidentes, tablas = self._escenario_corredor()
        reglas = reglas_activas_default()
        reglas["ALT005"] = make_regla(
            codigo="ALT005", activa=True, configuracion={"genera_observaciones": False}
        )
        resultado = ejecutar_motor_reglas(incidentes, incidentes, reglas, tablas, [])
        alertas = [a for a in resultado.alertas if a.tipo_alerta == "ALT005" and not a.es_grupo]
        assert len(alertas) == 2
        assert [a for a in resultado.alertas if a.es_grupo] == []

    def test_no_esta_en_reglas_activas_default_no_genera_alerta_grupo(self) -> None:
        """`reglas_activas_default()` no incluye ALT005 (ver su docstring) — mismo
        escenario que arriba, sin forzar `activa=True`, no genera nada. No confundir
        con el default real de producción, que sí la tiene activa."""
        incidentes, tablas = self._escenario_corredor()
        resultado = ejecutar_motor_reglas(
            incidentes, incidentes, reglas_activas_default(), tablas, []
        )
        assert [a for a in resultado.alertas if a.es_grupo] == []

    def test_alerta_individual_coexiste_con_alerta_agrupada(self) -> None:
        """Los dos caminos corren juntos para la misma regla activa, sin excluirse —
        igual que en producción real (81 alertas + 22 agrupadas sobre la misma
        corrida en el legacy)."""
        incidentes, tablas = self._escenario_corredor()
        reglas = reglas_activas_default()
        reglas["ALT005"] = make_regla(codigo="ALT005", activa=True)
        resultado = ejecutar_motor_reglas(incidentes, incidentes, reglas, tablas, [])
        individuales = [
            a for a in resultado.alertas if a.tipo_alerta == "ALT005" and not a.es_grupo
        ]
        assert len(individuales) == 2  # una por incidente, cada uno cita al otro
        assert len([a for a in resultado.alertas if a.es_grupo]) == 1  # el grupo sigue generándose

    def test_dispara_duplicado_por_misma_localidad(self) -> None:
        liquidacion_id = uuid.uuid4()
        fecha = date(2026, 1, 15)
        tabla1 = make_tabla_km(
            localidad_cliente="Rafaela", empresa_nombre="E", sucursal_nombre="S1"
        )
        tabla2 = make_tabla_km(
            localidad_cliente="RAFAELA", empresa_nombre="E", sucursal_nombre="S2"
        )
        inc1 = make_incidente(
            numero_incidente="100",
            liquidacion_id=liquidacion_id,
            empresa_nombre="E",
            sucursal_nombre="S1",
            fecha_cierre=fecha,
            cant_km_cobrado=50.0,
        )
        inc2 = make_incidente(
            numero_incidente="200",
            liquidacion_id=liquidacion_id,
            empresa_nombre="E",
            sucursal_nombre="S2",
            fecha_cierre=fecha,
            cant_km_cobrado=60.0,
        )
        reglas = reglas_activas_default()
        reglas["ALT005"] = make_regla(codigo="ALT005", activa=True)
        resultado = ejecutar_motor_reglas([inc1, inc2], [inc1, inc2], reglas, [tabla1, tabla2], [])
        alertas1 = [
            a
            for a in resultado.alertas
            if a.tipo_alerta == "ALT005" and not a.es_grupo and a.incidente_id == inc1.id
        ]
        assert len(alertas1) == 1
        assert alertas1[0].datos_contexto == {
            "tipo": "duplicado",
            "cobrado_este": 50.0,
            "otros_incidentes": ["200"],
            "localidad": "Rafaela",
        }
        # simétrico: inc2 también dispara la suya citando a inc1 — cada incidente se
        # evalúa por su cuenta, igual que el legacy.
        alertas2 = [
            a
            for a in resultado.alertas
            if a.tipo_alerta == "ALT005" and not a.es_grupo and a.incidente_id == inc2.id
        ]
        assert len(alertas2) == 1
        assert alertas2[0].datos_contexto["otros_incidentes"] == ["100"]

    def test_dispara_corredor_duplicado(self) -> None:
        spst_id = uuid.uuid4()
        liquidacion_id = uuid.uuid4()
        fecha = date(2026, 1, 15)
        tabla1 = make_tabla_km(
            spst_id=spst_id,
            kms_recorrido=100.0,
            localidad_cliente="A",
            empresa_nombre="E",
            sucursal_nombre="S1",
        )
        tabla2 = make_tabla_km(
            spst_id=spst_id,
            kms_recorrido=130.0,  # diferencia 30 <= 50 -> mismo corredor
            localidad_cliente="B",  # distinta localidad -> no matchea "exactos"
            empresa_nombre="E",
            sucursal_nombre="S2",
        )
        inc1 = make_incidente(
            numero_incidente="300",
            liquidacion_id=liquidacion_id,
            empresa_nombre="E",
            sucursal_nombre="S1",
            fecha_cierre=fecha,
            cant_km_cobrado=40.0,
        )
        inc2 = make_incidente(
            numero_incidente="400",
            liquidacion_id=liquidacion_id,
            empresa_nombre="E",
            sucursal_nombre="S2",
            fecha_cierre=fecha,
            cant_km_cobrado=35.0,
        )
        reglas = reglas_activas_default()
        reglas["ALT005"] = make_regla(codigo="ALT005", activa=True)
        resultado = ejecutar_motor_reglas([inc1, inc2], [inc1, inc2], reglas, [tabla1, tabla2], [])
        alertas1 = [
            a
            for a in resultado.alertas
            if a.tipo_alerta == "ALT005" and not a.es_grupo and a.incidente_id == inc1.id
        ]
        assert len(alertas1) == 1
        assert alertas1[0].datos_contexto == {
            "tipo": "corredor_duplicado",
            "cobrado_este": 40.0,
            "km_actual": 100.0,
            "otros_incidentes": ["400"],
            "spst_id": str(spst_id),
        }

    def test_dispara_corredor_contenido_solo_si_ningun_hermano_cobro_km(self) -> None:
        spst_id = uuid.uuid4()
        liquidacion_id = uuid.uuid4()
        fecha = date(2026, 1, 15)
        tabla1 = make_tabla_km(
            spst_id=spst_id,
            kms_recorrido=100.0,
            localidad_cliente="A",
            empresa_nombre="E",
            sucursal_nombre="S1",
        )
        tabla2 = make_tabla_km(
            spst_id=spst_id,
            kms_recorrido=120.0,
            localidad_cliente="B",
            empresa_nombre="E",
            sucursal_nombre="S2",
        )
        inc1 = make_incidente(
            numero_incidente="500",
            liquidacion_id=liquidacion_id,
            empresa_nombre="E",
            sucursal_nombre="S1",
            fecha_cierre=fecha,
            cant_km_cobrado=45.0,
        )
        inc2 = make_incidente(
            numero_incidente="600",
            liquidacion_id=liquidacion_id,
            empresa_nombre="E",
            sucursal_nombre="S2",
            fecha_cierre=fecha,
            cant_km_cobrado=0.0,  # el hermano no cobró km -> rama de prioridad 2
        )
        reglas = reglas_activas_default()
        reglas["ALT005"] = make_regla(codigo="ALT005", activa=True)
        resultado = ejecutar_motor_reglas([inc1, inc2], [inc1, inc2], reglas, [tabla1, tabla2], [])
        alertas = [a for a in resultado.alertas if a.tipo_alerta == "ALT005"]
        assert len(alertas) == 1  # inc2 no dispara nada (guarda G2: km cobrado == 0)
        assert alertas[0].incidente_id == inc1.id
        assert alertas[0].datos_contexto == {
            "tipo": "corredor_contenido",
            "cobrado_este": 45.0,
            "km_actual": 100.0,
            "otros_incidentes": ["600"],
            "spst_id": str(spst_id),
        }

    def test_exactos_y_corredor_son_disjuntos(self) -> None:
        """Un vecino que matchea por localidad Y por corredor a la vez solo cuenta
        una vez, en `exactos` — no genera además una alerta de corredor duplicada."""
        spst_id = uuid.uuid4()
        liquidacion_id = uuid.uuid4()
        fecha = date(2026, 1, 15)
        tabla1 = make_tabla_km(
            spst_id=spst_id,
            kms_recorrido=100.0,
            localidad_cliente="Rafaela",
            empresa_nombre="E",
            sucursal_nombre="S1",
        )
        tabla2 = make_tabla_km(
            spst_id=spst_id,
            kms_recorrido=110.0,  # dentro del umbral -> también matchearía corredor
            localidad_cliente="Rafaela",  # misma localidad -> matchea "exactos"
            empresa_nombre="E",
            sucursal_nombre="S2",
        )
        inc1 = make_incidente(
            numero_incidente="700",
            liquidacion_id=liquidacion_id,
            empresa_nombre="E",
            sucursal_nombre="S1",
            fecha_cierre=fecha,
            cant_km_cobrado=50.0,
        )
        inc2 = make_incidente(
            numero_incidente="800",
            liquidacion_id=liquidacion_id,
            empresa_nombre="E",
            sucursal_nombre="S2",
            fecha_cierre=fecha,
            cant_km_cobrado=55.0,
        )
        reglas = reglas_activas_default()
        reglas["ALT005"] = make_regla(codigo="ALT005", activa=True)
        resultado = ejecutar_motor_reglas([inc1, inc2], [inc1, inc2], reglas, [tabla1, tabla2], [])
        alertas1 = [
            a for a in resultado.alertas if a.tipo_alerta == "ALT005" and a.incidente_id == inc1.id
        ]
        assert len(alertas1) == 1
        assert alertas1[0].datos_contexto["tipo"] == "duplicado"

    def test_maximo_dos_alertas_por_incidente(self) -> None:
        """Un incidente con un vecino solo-por-localidad y otro solo-por-corredor
        dispara los dos caminos a la vez — el tope real del legacy es 2."""
        spst_id = uuid.uuid4()
        liquidacion_id = uuid.uuid4()
        fecha = date(2026, 1, 15)
        tabla_actual = make_tabla_km(
            spst_id=spst_id,
            kms_recorrido=100.0,
            localidad_cliente="Rafaela",
            empresa_nombre="E",
            sucursal_nombre="S1",
        )
        tabla_localidad = make_tabla_km(
            spst_id=None,  # sin SPST -> nunca matchea "corredor"
            localidad_cliente="Rafaela",
            empresa_nombre="E",
            sucursal_nombre="S2",
        )
        tabla_corredor = make_tabla_km(
            spst_id=spst_id,
            kms_recorrido=120.0,
            localidad_cliente="Otra Ciudad",  # distinta -> no matchea "exactos"
            empresa_nombre="E",
            sucursal_nombre="S3",
        )
        inc_actual = make_incidente(
            numero_incidente="900",
            liquidacion_id=liquidacion_id,
            empresa_nombre="E",
            sucursal_nombre="S1",
            fecha_cierre=fecha,
            cant_km_cobrado=45.0,
        )
        inc_localidad = make_incidente(
            numero_incidente="901",
            liquidacion_id=liquidacion_id,
            empresa_nombre="E",
            sucursal_nombre="S2",
            fecha_cierre=fecha,
            cant_km_cobrado=50.0,
        )
        inc_corredor = make_incidente(
            numero_incidente="902",
            liquidacion_id=liquidacion_id,
            empresa_nombre="E",
            sucursal_nombre="S3",
            fecha_cierre=fecha,
            cant_km_cobrado=55.0,
        )
        reglas = reglas_activas_default()
        reglas["ALT005"] = make_regla(codigo="ALT005", activa=True)
        resultado = ejecutar_motor_reglas(
            [inc_actual, inc_localidad, inc_corredor],
            [inc_actual, inc_localidad, inc_corredor],
            reglas,
            [tabla_actual, tabla_localidad, tabla_corredor],
            [],
        )
        alertas = [
            a
            for a in resultado.alertas
            if a.tipo_alerta == "ALT005" and a.incidente_id == inc_actual.id
        ]
        assert len(alertas) == 2
        tipos = {a.datos_contexto["tipo"] for a in alertas}
        assert tipos == {"duplicado", "corredor_duplicado"}

    def test_no_dispara_sin_fecha_cierre(self) -> None:
        tabla = make_tabla_km(localidad_cliente="Rafaela")
        vecino_tabla = make_tabla_km(
            localidad_cliente="Rafaela", empresa_nombre="E2", sucursal_nombre="S2"
        )
        incidente = make_incidente(
            empresa_nombre=tabla.empresa_nombre,
            sucursal_nombre=tabla.sucursal_nombre,
            fecha_cierre=None,
            cant_km_cobrado=50.0,
        )
        vecino = make_incidente(
            empresa_nombre="E2", sucursal_nombre="S2", fecha_cierre=None, cant_km_cobrado=50.0
        )
        reglas = reglas_activas_default()
        reglas["ALT005"] = make_regla(codigo="ALT005", activa=True)
        resultado = ejecutar_motor_reglas(
            [incidente, vecino], [incidente, vecino], reglas, [tabla, vecino_tabla], []
        )
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT005"] == []

    def test_no_dispara_sin_km_cobrado(self) -> None:
        incidentes, tablas = self._escenario_corredor()
        incidente_sin_km = make_incidente(
            liquidacion_id=incidentes[0].liquidacion_id,
            empresa_nombre="E",
            sucursal_nombre="S1",
            fecha_cierre=date(2026, 1, 15),
            cant_km_cobrado=0.0,
        )
        reglas = reglas_activas_default()
        reglas["ALT005"] = make_regla(codigo="ALT005", activa=True)
        resultado = ejecutar_motor_reglas(
            [incidente_sin_km, incidentes[1]], [incidente_sin_km, incidentes[1]], reglas, tablas, []
        )
        alertas = [
            a
            for a in resultado.alertas
            if a.tipo_alerta == "ALT005" and a.incidente_id == incidente_sin_km.id
        ]
        assert alertas == []

    def test_no_dispara_sin_tabla_km_resoluble(self) -> None:
        incidente = make_incidente(
            empresa_nombre="Sin Tabla", sucursal_nombre="Sin Tabla", cant_km_cobrado=50.0
        )
        reglas = reglas_activas_default()
        reglas["ALT005"] = make_regla(codigo="ALT005", activa=True)
        resultado = ejecutar_motor_reglas([incidente], [incidente], reglas, [], [])
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT005"] == []

    def test_no_dispara_sin_vecinos_mismo_dia(self) -> None:
        tabla = make_tabla_km(localidad_cliente="Rafaela")
        incidente = make_incidente(
            empresa_nombre=tabla.empresa_nombre,
            sucursal_nombre=tabla.sucursal_nombre,
            cant_km_cobrado=50.0,
        )
        reglas = reglas_activas_default()
        reglas["ALT005"] = make_regla(codigo="ALT005", activa=True)
        resultado = ejecutar_motor_reglas([incidente], [incidente], reglas, [tabla], [])
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT005"] == []


class TestAlt008TarifarioInexistente:
    def test_no_dispara_cuando_existe_tarifario(self) -> None:
        tarifario = make_tarifario(tipo_servicio="correctivo")
        incidente = make_incidente(tipo="correctivo")
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [tarifario]
        )
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT008"] == []

    def test_dispara_cuando_no_existe_tarifario_para_el_tipo(self) -> None:
        tarifario = make_tarifario(tipo_servicio="preventivo")
        incidente = make_incidente(tipo="correctivo")
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [tarifario]
        )
        alertas = [a for a in resultado.alertas if a.tipo_alerta == "ALT008"]
        assert len(alertas) == 1
        assert alertas[0].datos_contexto["tipo_servicio"] == "correctivo"
        assert alertas[0].datos_contexto["spst_id"] is None

    def test_contexto_incluye_el_spst_resuelto(self) -> None:
        """El `spst_id` viaja en `datos_contexto` para que la UI pueda linkear
        directo a "+ Nueva tarifa" con el SPST correcto, en vez de que la TL
        adivine."""
        spst_id = uuid.uuid4()
        tabla = make_tabla_km(spst_id=spst_id)
        incidente = make_incidente(
            tipo="correctivo",
            empresa_nombre=tabla.empresa_nombre,
            sucursal_nombre=tabla.sucursal_nombre,
        )
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [tabla], []
        )
        alertas = [a for a in resultado.alertas if a.tipo_alerta == "ALT008"]
        assert len(alertas) == 1
        assert alertas[0].datos_contexto["spst_id"] == str(spst_id)


class TestAlt009ParEmpresaSucursal:
    def test_no_dispara_cuando_existe_el_par(self) -> None:
        tabla = make_tabla_km()
        incidente = make_incidente(
            empresa_nombre=tabla.empresa_nombre,
            sucursal_nombre=tabla.sucursal_nombre,
            cant_km_cobrado=10.0,
        )
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [tabla], []
        )
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT009"] == []

    def test_dispara_cuando_no_existe_el_par(self) -> None:
        incidente = make_incidente(
            empresa_nombre="Sin Registrar", sucursal_nombre="Sin Registrar", cant_km_cobrado=10.0
        )
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], []
        )
        assert len([a for a in resultado.alertas if a.tipo_alerta == "ALT009"]) == 1

    def test_no_dispara_cuando_no_cobro_kms_aunque_falte_el_par(self) -> None:
        incidente = make_incidente(
            empresa_nombre="Sin Registrar", sucursal_nombre="Sin Registrar", cant_km_cobrado=0.0
        )
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], []
        )
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT009"] == []


class TestMotorOrquestador:
    def test_regla_inactiva_no_genera_alerta(self) -> None:
        tarifario = make_tarifario(costo_servicio=1500.0)
        incidente = make_incidente(costo_servicio_cobrado=9999.0)
        reglas = reglas_activas_default()
        del reglas["ALT001"]
        resultado = ejecutar_motor_reglas([incidente], [incidente], reglas, [], [tarifario])
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT001"] == []

    def test_es_deterministico_entre_corridas(self) -> None:
        tarifario = make_tarifario(costo_servicio=1500.0)
        incidente = make_incidente(costo_servicio_cobrado=1800.0)
        r1 = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [tarifario]
        )
        r2 = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [tarifario]
        )
        assert len(r1.alertas) == len(r2.alertas) == 1

    def test_liquidacion_sin_incidentes_da_resultado_vacio(self) -> None:
        resultado = ejecutar_motor_reglas([], [], reglas_activas_default(), [], [])
        assert resultado.alertas == []
        assert resultado.incidentes_evaluados == []

    def test_estado_validacion_distingue_ok_de_con_alertas(self) -> None:
        tarifario = make_tarifario(costo_servicio=1500.0)
        inc_ok = make_incidente(numero_incidente="1", costo_servicio_cobrado=1500.0)
        inc_alerta = make_incidente(numero_incidente="2", costo_servicio_cobrado=9999.0)
        todos = [inc_ok, inc_alerta]
        resultado = ejecutar_motor_reglas(todos, todos, reglas_activas_default(), [], [tarifario])
        estados = {e.incidente_id: e.estado_validacion for e in resultado.incidentes_evaluados}
        assert estados[inc_ok.id] == "ok"
        assert estados[inc_alerta.id] == "con_alertas"
