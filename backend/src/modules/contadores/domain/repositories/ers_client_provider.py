from typing import Protocol

from src.modules.contadores.domain.entities.ers_client import ErsClient


class ErsClientProvider(Protocol):
    """Puerto de dominio para interactuar con Epson Remote Services (ERS).

    La implementación concreta vive en infrastructure/ers/httpx_ers_client_provider.py.
    """

    async def list_active_customers(self) -> list[ErsClient]:
        """Obtiene los grupos de dispositivos desde ERS formateados como clientes."""
        ...

    async def export_meters_to_csv(
        self,
        *,
        group_id: str,
        group_name: str,
        max_date: str,
        output_dir: str,
        suma_color: bool = False,
    ) -> str:
        """Extrae la telemetría de dispositivos de un grupo ERS y los exporta a CSV.

        Returns:
            Path local del archivo CSV generado.
        """
        ...
