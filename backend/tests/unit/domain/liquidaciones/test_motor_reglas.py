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
            [incidente], [incidente], reglas_activas_default(), [], [], [tarifario]
        )
        assert resultado.alertas == []
        assert resultado.incidentes_evaluados[0].costo_servicio_esperado == 1500.0

    def test_dispara_cuando_difiere_del_tarifario(self) -> None:
        tarifario = make_tarifario(costo_servicio=1500.0)
        incidente = make_incidente(costo_servicio_cobrado=1800.0)
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [], [tarifario]
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
            [incidente], [incidente], reglas_activas_default(), [], [], [tarifario]
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
            [incidente], [incidente], reglas_activas_default(), [tabla], [], []
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
            [incidente], [incidente], reglas_activas_default(), [tabla], [], []
        )
        alertas = [a for a in resultado.alertas if a.tipo_alerta == "ALT002"]
        assert len(alertas) == 1
        assert alertas[0].datos_contexto["diferencia"] == 40.0

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
            [inc_a, inc_b],
            [inc_a, inc_b],
            reglas_activas_default(),
            [tabla_a, tabla_b],
            [],
            [],
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
        resultado = ejecutar_motor_reglas(todos, todos, reglas_activas_default(), [], [], [])
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
        resultado = ejecutar_motor_reglas(todos, todos, reglas_activas_default(), [], [], [])
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
        resultado = ejecutar_motor_reglas(todos, todos, reglas, [], [], [])
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT003"] == []


class TestAlt004ServicioDuplicado:
    def test_no_dispara_con_numero_unico(self) -> None:
        incidente = make_incidente(numero_incidente="500")
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [], []
        )
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT004"] == []

    def test_dispara_cuando_ya_fue_liquidado_antes(self) -> None:
        liq_previa = uuid.uuid4()
        inc_actual = make_incidente(numero_incidente="500")
        inc_previo = make_incidente(numero_incidente="500", liquidacion_id=liq_previa)
        resultado = ejecutar_motor_reglas(
            [inc_actual],
            [inc_actual, inc_previo],
            reglas_activas_default(),
            [],
            [],
            [],
        )
        alertas = [a for a in resultado.alertas if a.tipo_alerta == "ALT004"]
        assert len(alertas) == 1
        assert alertas[0].datos_contexto["liquidaciones_previas"] == [str(liq_previa)]


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

    def test_un_solo_incidente_no_genera_observacion(self) -> None:
        tabla = make_tabla_km(localidad_cliente="Rafaela")
        incidente = make_incidente(
            empresa_nombre=tabla.empresa_nombre,
            sucursal_nombre=tabla.sucursal_nombre,
            cant_km_cobrado=50.0,
        )
        reglas = reglas_activas_default()
        reglas["ALT005"] = make_regla(codigo="ALT005", activa=True)
        resultado = ejecutar_motor_reglas([incidente], [incidente], reglas, [tabla], [], [])
        assert resultado.observaciones == []

    def test_grupo_activo_genera_observacion_critica(self) -> None:
        incidentes, tablas = self._escenario_corredor()
        reglas = reglas_activas_default()
        reglas["ALT005"] = make_regla(codigo="ALT005", activa=True)
        resultado = ejecutar_motor_reglas(incidentes, incidentes, reglas, tablas, [], [])
        assert len(resultado.observaciones) == 1
        obs = resultado.observaciones[0]
        assert obs.tipo_observacion == "RUTA_COMPARTIDA"
        assert obs.severidad == "CRITICO"
        assert set(obs.incidentes_relacionados) == {i.id for i in incidentes}

    def test_desactivada_por_default_no_genera_observacion(self) -> None:
        """`activa=False` es el default real de `seed.py` — mismo escenario que
        arriba, sin forzar `activa=True`, no genera nada."""
        incidentes, tablas = self._escenario_corredor()
        resultado = ejecutar_motor_reglas(
            incidentes, incidentes, reglas_activas_default(), tablas, [], []
        )
        assert resultado.observaciones == []


class TestAlt008TarifarioInexistente:
    def test_no_dispara_cuando_existe_tarifario(self) -> None:
        tarifario = make_tarifario(tipo_servicio="correctivo")
        incidente = make_incidente(tipo="correctivo")
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [], [tarifario]
        )
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT008"] == []

    def test_dispara_cuando_no_existe_tarifario_para_el_tipo(self) -> None:
        tarifario = make_tarifario(tipo_servicio="preventivo")
        incidente = make_incidente(tipo="correctivo")
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [], [tarifario]
        )
        alertas = [a for a in resultado.alertas if a.tipo_alerta == "ALT008"]
        assert len(alertas) == 1
        assert alertas[0].datos_contexto["tipo_servicio"] == "correctivo"


class TestAlt009ParEmpresaSucursal:
    def test_no_dispara_cuando_existe_el_par(self) -> None:
        tabla = make_tabla_km()
        incidente = make_incidente(
            empresa_nombre=tabla.empresa_nombre,
            sucursal_nombre=tabla.sucursal_nombre,
            cant_km_cobrado=10.0,
        )
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [tabla], [], []
        )
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT009"] == []

    def test_dispara_cuando_no_existe_el_par(self) -> None:
        incidente = make_incidente(
            empresa_nombre="Sin Registrar", sucursal_nombre="Sin Registrar", cant_km_cobrado=10.0
        )
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [], []
        )
        assert len([a for a in resultado.alertas if a.tipo_alerta == "ALT009"]) == 1

    def test_no_dispara_cuando_no_cobro_kms_aunque_falte_el_par(self) -> None:
        incidente = make_incidente(
            empresa_nombre="Sin Registrar", sucursal_nombre="Sin Registrar", cant_km_cobrado=0.0
        )
        resultado = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [], []
        )
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT009"] == []


class TestMotorOrquestador:
    def test_regla_inactiva_no_genera_alerta(self) -> None:
        tarifario = make_tarifario(costo_servicio=1500.0)
        incidente = make_incidente(costo_servicio_cobrado=9999.0)
        reglas = reglas_activas_default()
        del reglas["ALT001"]
        resultado = ejecutar_motor_reglas([incidente], [incidente], reglas, [], [], [tarifario])
        assert [a for a in resultado.alertas if a.tipo_alerta == "ALT001"] == []

    def test_es_deterministico_entre_corridas(self) -> None:
        tarifario = make_tarifario(costo_servicio=1500.0)
        incidente = make_incidente(costo_servicio_cobrado=1800.0)
        r1 = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [], [tarifario]
        )
        r2 = ejecutar_motor_reglas(
            [incidente], [incidente], reglas_activas_default(), [], [], [tarifario]
        )
        assert len(r1.alertas) == len(r2.alertas) == 1

    def test_liquidacion_sin_incidentes_da_resultado_vacio(self) -> None:
        resultado = ejecutar_motor_reglas([], [], reglas_activas_default(), [], [], [])
        assert resultado.alertas == []
        assert resultado.observaciones == []
        assert resultado.incidentes_evaluados == []

    def test_estado_validacion_distingue_ok_de_con_alertas(self) -> None:
        tarifario = make_tarifario(costo_servicio=1500.0)
        inc_ok = make_incidente(numero_incidente="1", costo_servicio_cobrado=1500.0)
        inc_alerta = make_incidente(numero_incidente="2", costo_servicio_cobrado=9999.0)
        todos = [inc_ok, inc_alerta]
        resultado = ejecutar_motor_reglas(
            todos, todos, reglas_activas_default(), [], [], [tarifario]
        )
        estados = {e.incidente_id: e.estado_validacion for e in resultado.incidentes_evaluados}
        assert estados[inc_ok.id] == "ok"
        assert estados[inc_alerta.id] == "con_alertas"
