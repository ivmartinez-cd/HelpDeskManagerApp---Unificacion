from typing import Protocol


class ClienteSigesMapRepository(Protocol):
    """Alias manual `cliente` de Gestión → `ID_Empresa`(s) de Siges, para los
    nombres que el cruce automático no resuelve (ver cliente_matcher). El
    alias siempre gana sobre el cruce automático; un cliente con varias
    empresas mapeadas suma las impresoras de todas."""

    async def list_all(self) -> dict[str, list[int]]: ...

    async def replace(self, cliente_gestion: str, siges_empresa_ids: list[int]) -> None:
        """Reemplaza el mapeo completo del cliente (lista vacía = desmapear)."""
        ...
