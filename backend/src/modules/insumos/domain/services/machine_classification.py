"""Clasificación de la respuesta de getMachineBySerial como CdVerdict."""

from src.modules.insumos.domain.services.company_matching import same_company
from src.modules.insumos.domain.value_objects.cd_supply import CdMachine


def classify_machine(machine: CdMachine | None, customer_name: str) -> tuple[str, str]:
    """Traduce la respuesta de getMachineBySerial a (cd_status, cd_detail).

    machine=None → BODEGA: el SOAP devolvió lista vacía (equipo sin asignar a ninguna
    empresa en Canal Directo), único estado habilitado para baja masiva.

    machine con empresa que no matchea al cliente auditado → OTRO_CLIENTE: informativo,
    no habilita la baja — el nombre de Canal Directo no es fuente confiable de movimiento
    (puede aparecer un cliente nuevo sin alias registrado).

    Cualquier otro caso → EN_CLIENTE.
    """
    if machine is None:
        return "BODEGA", "Sin asignar en Canal Directo"

    detail = " · ".join(
        p for p in (machine.estado, machine.empresa_name, machine.sucursal_name) if p
    )

    if machine.empresa_name and customer_name and not same_company(
        machine.empresa_name, customer_name
    ):
        return "OTRO_CLIENTE", detail
    return "EN_CLIENTE", detail
