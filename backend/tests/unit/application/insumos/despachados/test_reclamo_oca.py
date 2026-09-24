"""Caso de uso "Reclamar en OCA": arma contacto, operativa y comentario desde la base de
HDM (fakes en memoria)."""

import pytest

from src.modules.insumos.application.use_cases.despachados.consultas_despachos import (
    ObtenerDetalleDespacho,
)
from src.modules.insumos.application.use_cases.despachados.reclamo_oca import (
    PrepararReclamoOca,
)
from src.modules.insumos.domain.errores_despachados import EnvioDespachoNoEncontradoError
from src.modules.insumos.domain.value_objects.despachados.reclamo_oca import (
    ContactoReclamoOca,
    ReglaContactoReclamo,
)
from tests.unit.application.insumos.despachados.fakes_consulta_despachos import (
    CONFIG,
    MundoConsulta,
)
from tests.unit.application.insumos.despachados.fakes_despachados import (
    despacho,
    envio,
    estado_oca,
)

GUIA_CORREO = "2610800000000000001"
CONTACTO = ContactoReclamoOca("Canal Directo", "SI", "CDSI", "a@x.com", "30709381101", "")
REGLAS = (ReglaContactoReclamo(prefijo="26108", cuenta="434324", contacto=CONTACTO),)


def _caso(mundo: MundoConsulta) -> PrepararReclamoOca:
    return PrepararReclamoOca(ObtenerDetalleDespacho(mundo.ports(), CONFIG), REGLAS)


async def test_arma_el_reclamo_con_contacto_operativa_y_comentario() -> None:
    mundo = MundoConsulta()
    mundo.envios.envios[GUIA_CORREO] = envio(
        GUIA_CORREO, estado_oca=estado_oca(GUIA_CORREO, operativa="434305")
    )
    await mundo.remitos.guardar([despacho(GUIA_CORREO)])

    reclamo = await _caso(mundo).execute(GUIA_CORREO)

    assert (reclamo.guia, reclamo.operativa, reclamo.contacto) == (
        GUIA_CORREO,
        "434305",
        CONTACTO,
    )
    assert reclamo.comentario.startswith(f"Reclamo por el envío {GUIA_CORREO}.")
    assert "Remito: 50001 (1 bulto)." in reclamo.comentario


async def test_guia_sin_estado_de_oca_ni_regla_va_sin_operativa_ni_contacto() -> None:
    mundo = MundoConsulta()
    mundo.envios.envios["3867500000000000001"] = envio()

    reclamo = await _caso(mundo).execute("3867500000000000001")

    assert (reclamo.operativa, reclamo.contacto) == ("", None)


async def test_guia_que_no_se_sigue_es_404() -> None:
    with pytest.raises(EnvioDespachoNoEncontradoError):
        await _caso(MundoConsulta()).execute(GUIA_CORREO)
