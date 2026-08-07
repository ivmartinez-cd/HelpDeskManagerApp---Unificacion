from typing import Protocol

from src.modules.contadores.domain.entities.sds_client import SdsClient


class SdsClientProvider(Protocol):
    """Puerto de dominio para interactuar con la API externa de HP SDS.

    La implementación concreta vive en infrastructure/sds/httpx_sds_client_provider.py.
    """

    async def list_active_customers(self) -> list[SdsClient]:
        """Obtiene la lista de clientes activos desde la API de SDS."""
        ...

    async def export_meters_to_csv(
        self,
        *,
        customer_id: str,
        customer_name: str,
        max_date: str,
        output_dir: str,
        suma_color: bool = False,
    ) -> str:
        """Descarga contadores de SDS para un cliente y los exporta a CSV.

        Returns:
            Path local del archivo CSV generado.
        """
        ...
