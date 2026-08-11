"""Detección de caídas de colector y salidas masivas de equipos.

Dos señales complementarias:
- detect_monitor_outages: señal real de /api/monitors (colector confirmado caído).
  Sin umbral de cantidad — cualquier grupo bajo un colector offline se excluye.
- detect_mass_outages: heurística de respaldo para equipos sin monitor_name o con
  colector activo pero muchos equipos desconectados el mismo día (red/sitio caído).

detect_outages combina las dos: aplica la señal real primero y la heurística sobre el
resto (sin re-sort global — el orden de cada señal se preserva independientemente).
"""

from collections import defaultdict

from src.modules.insumos.domain.value_objects.dca_monitor import MonitorKey
from src.modules.insumos.domain.value_objects.offline_clock import outage_day
from src.modules.insumos.domain.value_objects.offline_device import MassOutage, OfflineDevice

_MASS_OUTAGE_MIN_DEVICES = 5
_MASS_OUTAGE_MIN_PERCENT = 10


def detect_monitor_outages(
    devices: list[OfflineDevice],
    offline_monitor_keys: set[MonitorKey],
) -> list[MassOutage]:
    """Agrupa equipos cuyo colector está confirmado caído (señal real de Insight).

    Usa MonitorKey (customer_id + monitor_name) en lugar del monitor_name solo — esto evita
    que colectores homónimos de clientes distintos se contaminen entre sí (bug 3 del legacy).
    """
    if not offline_monitor_keys:
        return []
    groups: dict[tuple[int, str], list[OfflineDevice]] = defaultdict(list)
    for d in devices:
        if not d.monitor_name:
            continue
        if MonitorKey(d.customer_id, d.monitor_name) in offline_monitor_keys:
            groups[(d.customer_id, d.monitor_name)].append(d)

    outages = [
        MassOutage(
            customer_id=customer_id,
            customer_name=devices[0].customer_name,
            day=min(
                (outage_day(d.last_contact) for d in devices if d.last_contact),
                default="",
            ),
            device_ids=tuple(d.device_id for d in devices),
            confirmed=True,
            monitor_name=monitor_name,
        )
        for (customer_id, monitor_name), devices in groups.items()
    ]
    outages.sort(key=lambda o: len(o.device_ids), reverse=True)
    return outages


def detect_mass_outages(
    devices: list[OfflineDevice],
    fleet_sizes: dict[int, int],
    min_devices: int = _MASS_OUTAGE_MIN_DEVICES,
    online_customer_ids: set[int] | None = None,
    min_percent: int = _MASS_OUTAGE_MIN_PERCENT,
) -> list[MassOutage]:
    """Heurística de respaldo: agrupa equipos offline por (cliente, día UTC de last_contact)
    y devuelve los grupos que superan el doble umbral (cantidad Y porcentaje de la flota).

    fleet_sizes={}: fleet == 0 saltea el chequeo de %. División float para que 5/48 = 10.41%
    pase el umbral de min_percent=10 (el legacy usaba /, no //).
    """
    groups: dict[tuple[int, str], list[OfflineDevice]] = defaultdict(list)
    for d in devices:
        if not d.last_contact:
            continue
        day = outage_day(d.last_contact)
        groups[(d.customer_id, day)].append(d)

    outages = []
    for (customer_id, day), group_devices in groups.items():
        fleet = fleet_sizes.get(customer_id, 0)
        count = len(group_devices)
        if count < min_devices:
            continue
        if fleet > 0 and (count * 100 / fleet) < min_percent:
            continue
        outages.append(
            MassOutage(
                customer_id=customer_id,
                customer_name=group_devices[0].customer_name,
                day=day,
                device_ids=tuple(d.device_id for d in group_devices),
                fleet_size=fleet,
                monitor_online=(
                    customer_id in online_customer_ids if online_customer_ids else False
                ),
            )
        )
    outages.sort(key=lambda o: len(o.device_ids), reverse=True)
    return outages


def detect_outages(
    devices: list[OfflineDevice],
    fleet_sizes: dict[int, int],
    offline_monitor_keys: set[MonitorKey],
    min_devices: int = _MASS_OUTAGE_MIN_DEVICES,
    online_customer_ids: set[int] | None = None,
    min_percent: int = _MASS_OUTAGE_MIN_PERCENT,
) -> list[MassOutage]:
    """Combina señal real + heurística de respaldo. El orden de cada señal se preserva;
    no hay re-sort global (el legacy tampoco lo hacía y los tests lo asertan)."""
    monitor_outages = detect_monitor_outages(devices, offline_monitor_keys)
    monitor_excluded = {did for o in monitor_outages for did in o.device_ids}
    remaining = [d for d in devices if d.device_id not in monitor_excluded]
    heuristic_outages = detect_mass_outages(
        remaining, fleet_sizes, min_devices, online_customer_ids, min_percent
    )
    return monitor_outages + heuristic_outages
