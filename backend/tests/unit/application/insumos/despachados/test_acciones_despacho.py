"""Tests de RegistrarAccionDespacho y CerrarAlertaDespacho."""

from dataclasses import replace
from datetime import date, timedelta

import pytest

from src.modules.insumos.application.use_cases.despachados.acciones_despacho import (
    LARGO_MAXIMO_DETALLE,
    AccionDespachoPorts,
    CerrarAlertaDespacho,
    DatosAccion,
    RegistrarAccionDespacho,
    UsuarioActuante,
)
from src.modules.insumos.domain.entities.despachados.accion_registrada import (
    AccionRegistrada,
    ResultadoAccion,
    TipoAccion,
)
from src.modules.insumos.domain.entities.despachados.envio_seguido import CierreAlerta
from src.modules.insumos.domain.errores_despachados import (
    AccionDespachoInvalidaError,
    AlertaDespachoNoAbiertaError,
    CierreAlertaSinAccionError,
    EnvioDespachoNoEncontradoError,
)
from src.modules.insumos.domain.value_objects.despachados.clasificacion import ColorSemaforo
from tests.unit.application.insumos.despachados.fakes_despachados import (
    AHORA,
    GUIA_A,
    GUIA_B,
    USUARIO_ID,
    VERDE,
    FakeAccionesDespacho,
    FakeEnviosDespacho,
    envio,
)

ROJO = replace(VERDE, color=ColorSemaforo.ROJO, alerta=True, fecha_limite=date(2026, 9, 29))
USUARIO = UsuarioActuante(id=USUARIO_ID, nombre="Ana Operadora")
CIERRE_DE_ANA = CierreAlerta(
    cerrada_en=AHORA, usuario_id=USUARIO_ID, usuario_nombre="Ana Operadora"
)
CIERRE_ANTERIOR = replace(CIERRE_DE_ANA, cerrada_en=AHORA - timedelta(days=1), usuario_id=None)


def _datos(detalle: str = "Llamé al cliente", cerrar_alerta: bool = False) -> DatosAccion:
    return DatosAccion(
        tipo=TipoAccion.LLAMADO_CLIENTE,
        detalle=detalle,
        resultado=ResultadoAccion.PENDIENTE,
        cerrar_alerta=cerrar_alerta,
    )


class Mundo:
    def __init__(self) -> None:
        self.envios = FakeEnviosDespacho(
            [envio(GUIA_A, clasificacion=ROJO), envio(GUIA_B, clasificacion=VERDE)]
        )
        self.acciones = FakeAccionesDespacho()
        ports = AccionDespachoPorts(envios=self.envios, acciones=self.acciones, reloj=lambda: AHORA)
        self.registrar = RegistrarAccionDespacho(ports)
        self.cerrar = CerrarAlertaDespacho(ports)


class TestRegistrarAccion:
    async def test_guarda_la_accion_con_el_detalle_recortado(self) -> None:
        mundo = Mundo()

        accion = await mundo.registrar.execute(GUIA_A, _datos("  Llamé al cliente \n"), USUARIO)

        assert accion == AccionRegistrada(
            id=1,
            guia=GUIA_A,
            tipo=TipoAccion.LLAMADO_CLIENTE,
            detalle="Llamé al cliente",
            resultado=ResultadoAccion.PENDIENTE,
            cerro_alerta=False,
            usuario_id=USUARIO_ID,
            usuario_nombre="Ana Operadora",
            creada_en=AHORA,
        )
        assert mundo.acciones.acciones == [accion]
        assert (mundo.envios.cierres, mundo.envios.actualizados) == ([], [])

    async def test_puede_cerrar_la_alerta_abierta(self) -> None:
        mundo = Mundo()

        accion = await mundo.registrar.execute(GUIA_A, _datos(cerrar_alerta=True), USUARIO)

        assert accion.cerro_alerta is True
        assert mundo.envios.cierres == [(GUIA_A, CIERRE_DE_ANA)]
        assert mundo.envios.envios[GUIA_A].alerta_abierta is False

    async def test_el_cierre_escribe_solo_el_cierre_y_no_el_envio_entero(self) -> None:
        mundo = Mundo()

        await mundo.registrar.execute(GUIA_A, _datos(cerrar_alerta=True), USUARIO)

        assert mundo.envios.actualizados == []

    @pytest.mark.parametrize("detalle", ["", "   \n\t "])
    async def test_el_detalle_es_obligatorio(self, detalle: str) -> None:
        mundo = Mundo()

        with pytest.raises(AccionDespachoInvalidaError, match="El detalle es obligatorio"):
            await mundo.registrar.execute(GUIA_A, _datos(detalle), USUARIO)

        assert mundo.acciones.acciones == []

    async def test_el_detalle_admite_hasta_2000_caracteres(self) -> None:
        mundo = Mundo()
        al_limite = " " + "x" * LARGO_MAXIMO_DETALLE + " "

        accion = await mundo.registrar.execute(GUIA_A, _datos(al_limite), USUARIO)

        assert len(accion.detalle) == LARGO_MAXIMO_DETALLE
        with pytest.raises(AccionDespachoInvalidaError, match="2000"):
            await mundo.registrar.execute(GUIA_A, _datos(al_limite.strip() + "x"), USUARIO)

    async def test_la_guia_tiene_que_estar_seguida(self) -> None:
        mundo = Mundo()

        with pytest.raises(EnvioDespachoNoEncontradoError):
            await mundo.registrar.execute("3867500000009999999", _datos(), USUARIO)

    @pytest.mark.parametrize(
        "guia_y_cierre",
        [
            pytest.param((GUIA_B, None), id="sin-alerta"),
            pytest.param((GUIA_A, CIERRE_ANTERIOR), id="alerta-ya-cerrada"),
        ],
    )
    async def test_no_cierra_una_alerta_que_no_esta_abierta(
        self, guia_y_cierre: tuple[str, CierreAlerta | None]
    ) -> None:
        guia, cierre = guia_y_cierre
        mundo = Mundo()
        mundo.envios.envios[guia] = replace(mundo.envios.envios[guia], cierre_alerta=cierre)

        with pytest.raises(AlertaDespachoNoAbiertaError):
            await mundo.registrar.execute(guia, _datos(cerrar_alerta=True), USUARIO)

        assert mundo.acciones.acciones == []
        assert mundo.envios.cierres == []


class TestCerrarAlerta:
    async def test_cierra_la_alerta_si_hay_una_accion_registrada(self) -> None:
        mundo = Mundo()
        await mundo.registrar.execute(GUIA_A, _datos(), USUARIO)

        cerrado = await mundo.cerrar.execute(GUIA_A, USUARIO)

        assert cerrado.cierre_alerta == CIERRE_DE_ANA
        assert mundo.envios.envios[GUIA_A] == cerrado
        assert mundo.envios.cierres == [(GUIA_A, CIERRE_DE_ANA)]
        assert mundo.envios.actualizados == []

    async def test_sin_acciones_no_se_puede_cerrar(self) -> None:
        mundo = Mundo()

        with pytest.raises(CierreAlertaSinAccionError):
            await mundo.cerrar.execute(GUIA_A, USUARIO)

        assert mundo.envios.cierres == []

    async def test_la_guia_tiene_que_estar_seguida(self) -> None:
        with pytest.raises(EnvioDespachoNoEncontradoError):
            await Mundo().cerrar.execute("3867500000009999999", USUARIO)

    async def test_una_guia_sin_alerta_no_se_cierra(self) -> None:
        mundo = Mundo()
        await mundo.registrar.execute(GUIA_B, _datos(), USUARIO)

        with pytest.raises(AlertaDespachoNoAbiertaError):
            await mundo.cerrar.execute(GUIA_B, USUARIO)

    async def test_una_alerta_ya_cerrada_no_se_vuelve_a_cerrar(self) -> None:
        mundo = Mundo()
        await mundo.registrar.execute(GUIA_A, _datos(cerrar_alerta=True), USUARIO)

        with pytest.raises(AlertaDespachoNoAbiertaError):
            await mundo.cerrar.execute(GUIA_A, USUARIO)
