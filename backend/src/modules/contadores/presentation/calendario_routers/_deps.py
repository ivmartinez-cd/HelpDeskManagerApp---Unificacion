"""Permisos y constantes compartidos por los sub-routers del calendario."""

from fastapi import Depends

from src.modules.auth.presentation.dependencies.permissions import require_permission
from src.modules.contadores.domain.well_known_permissions import MANAGE, VIEW

require_view = Depends(require_permission(VIEW))
require_manage = Depends(require_permission(MANAGE))

# Un mes con muchos eventos de facturación no debería superar esto; si algún
# rango lo hace, subir el tope antes que silenciar la paginación.
MAX_PAGE_SIZE = 2000
# Ventana por defecto de "Sincronizar": no hay diff, así que cada sync rehace
# este rango entero con UNA consulta a la base de Gestión (ADR-047; los eventos
# ya traen su operador — ver SyncCalendarEventsUseCase). 90 días para cada
# lado cubre "todo lo vigente" (~1800 filas, de las que se muestran ~830).
DEFAULT_SYNC_WINDOW_DAYS = 90
# Corte del backlog de "pendientes" de la card de Inicio: 30 días de arrastre
# reciente. Queda dentro de la ventana de sync (±90), así que el corte manda
# antes que el borde de la copia local — ver GetPendingClientsUseCase.
DEFAULT_BACKLOG_DAYS = 30
# Operadores pool de Gestión sin persona real detrás: sus eventos no deben
# aparecer en el backlog de pendientes de nadie (ni de usuarios regulares
# ni del superadmin). Identificados por su id/login de Gestión.
POOL_BACKLOG_OPERADOR_IDS: frozenset[str] = frozenset({"contadores"})
