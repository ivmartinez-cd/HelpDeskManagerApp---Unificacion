"""Tests de las transiciones de estado hacia AyC — puerto de Web Agentes
(`LiquidationsController`/`view.ctp`), ver `transiciones_ayc.py`."""

import pytest

from src.modules.liquidaciones.domain.exceptions import TransicionEstadoAycInvalidaError
from src.modules.liquidaciones.domain.services.transiciones_ayc import (
    validar_anulable,
    validar_transicion,
)


class TestValidarTransicion:
    @pytest.mark.parametrize(
        ("verbo", "estado"),
        [
            ("recibir", "preliquidada"),
            ("recibir", "observada"),
            ("observar", "recibida"),
            ("observar", "aprobada"),
            ("aprobar", "recibida"),
            ("aprobar", "observada"),
        ],
    )
    def test_origenes_validos_no_lanzan(self, verbo: str, estado: str) -> None:
        validar_transicion(verbo, estado)  # no debe lanzar

    @pytest.mark.parametrize(
        ("verbo", "estado"),
        [
            ("recibir", "recibida"),
            ("recibir", "aprobada"),
            ("recibir", "cerrada"),
            ("observar", "preliquidada"),
            ("observar", "observada"),
            ("observar", "cerrada"),
            ("aprobar", "preliquidada"),
            ("aprobar", "aprobada"),
            ("aprobar", "cerrada"),
        ],
    )
    def test_origenes_invalidos_lanzan(self, verbo: str, estado: str) -> None:
        with pytest.raises(TransicionEstadoAycInvalidaError):
            validar_transicion(verbo, estado)


class TestValidarAnulable:
    @pytest.mark.parametrize(
        "estado", ["abierta", "preliquidada", "recibida", "observada", "aprobada"]
    )
    def test_no_cerrada_no_lanza(self, estado: str) -> None:
        validar_anulable(estado)  # no debe lanzar

    def test_cerrada_lanza(self) -> None:
        with pytest.raises(TransicionEstadoAycInvalidaError):
            validar_anulable("cerrada")
