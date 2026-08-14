"""Tests de la resolución manual de clientes sin cruce (búsqueda + mapeo)."""

from unittest.mock import AsyncMock

import pytest

from src.modules.contadores.application.use_cases.resolver_cliente_siges import (
    SearchEmpresasSiges,
    SetClienteSigesMap,
    SetClienteSigesMapCommand,
)
from src.modules.contadores.domain.ports.parque_cliente_port import EmpresaConParque


@pytest.mark.asyncio
async def test_search_delega_en_el_gateway() -> None:
    parque = AsyncMock()
    parque.search_empresas_activas.return_value = [
        EmpresaConParque(id=471, den_comercial="Gobierno de San Juan", impresoras=981)
    ]

    resultado = await SearchEmpresasSiges(parque).execute("San Juan")

    parque.search_empresas_activas.assert_awaited_once_with("San Juan")
    assert resultado[0].id == 471


@pytest.mark.asyncio
async def test_set_map_reemplaza_el_mapeo_del_cliente() -> None:
    alias = AsyncMock()

    await SetClienteSigesMap(alias).execute(
        SetClienteSigesMapCommand(
            cliente_gestion="  Gob San Juan  ", siges_empresa_ids=[471, 1375]
        )
    )

    alias.replace.assert_awaited_once_with("Gob San Juan", [471, 1375])


@pytest.mark.asyncio
async def test_set_map_con_lista_vacia_desmapea() -> None:
    alias = AsyncMock()

    await SetClienteSigesMap(alias).execute(
        SetClienteSigesMapCommand(cliente_gestion="Gob San Juan", siges_empresa_ids=[])
    )

    alias.replace.assert_awaited_once_with("Gob San Juan", [])
