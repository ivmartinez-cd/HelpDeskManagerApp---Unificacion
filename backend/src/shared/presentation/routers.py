"""Routers HTTP de todos los módulos, en el orden exacto en que `create_app`
los registra. Vivir acá (y no en app.py) es solo por tamaño: el orden es parte
del contrato."""

from fastapi import APIRouter

from src.modules.analisis_log_hp.presentation.analysis_router import (
    router as pi_analysis_router,
)
from src.modules.analisis_log_hp.presentation.cpmd_router import router as pi_cpmd_router
from src.modules.analisis_log_hp.presentation.error_codes_router import (
    router as pi_error_codes_router,
)
from src.modules.analisis_log_hp.presentation.saved_analyses_router import (
    router as pi_saved_analyses_router,
)
from src.modules.analisis_log_hp.presentation.sds_router import router as pi_sds_router
from src.modules.auth.presentation.admin_permissions_router import (
    router as admin_permissions_router,
)
from src.modules.auth.presentation.admin_users_router import router as admin_users_router
from src.modules.auth.presentation.auth_router import router as auth_router
from src.modules.auth.presentation.dashboard_prefs_router import router as dashboard_prefs_router
from src.modules.auth.presentation.route_visits_router import router as route_visits_router
from src.modules.contadores.presentation.anexos_pendientes_router import (
    router as anexos_pendientes_router,
)
from src.modules.contadores.presentation.calendario_router import (
    router as calendario_router,
)
from src.modules.contadores.presentation.clientes_nuevos_router import (
    router as clientes_nuevos_router,
)
from src.modules.contadores.presentation.equipos_sin_real_router import (
    router as equipos_sin_real_router,
)
from src.modules.contadores.presentation.ers_router import router as ers_router
from src.modules.contadores.presentation.ftp_clients_router import router as ftp_clients_router
from src.modules.contadores.presentation.sds_router import router as sds_router
from src.modules.contadores.presentation.tools_router import router as contadores_tools_router
from src.modules.insumos.presentation.alerts_router import router as insumos_alerts_router
from src.modules.insumos.presentation.audit_router import router as insumos_audit_router
from src.modules.insumos.presentation.config_router import router as insumos_config_router
from src.modules.insumos.presentation.customers_router import router as insumos_customers_router
from src.modules.insumos.presentation.devices_router import router as insumos_devices_router
from src.modules.insumos.presentation.health_router import router as insumos_health_router
from src.modules.insumos.presentation.mail_log_router import router as insumos_mail_log_router
from src.modules.insumos.presentation.new_devices_router import (
    router as insumos_new_devices_router,
)
from src.modules.insumos.presentation.offline_devices_router import (
    router as insumos_offline_devices_router,
)
from src.modules.insumos.presentation.requests_router import router as insumos_requests_router
from src.modules.insumos.presentation.statistics_router import (
    router as insumos_statistics_router,
)
from src.modules.liquidaciones.presentation.alertas_router import (
    router as liquidaciones_alertas_router,
)
from src.modules.liquidaciones.presentation.config_router import (
    router as liquidaciones_config_router,
)
from src.modules.liquidaciones.presentation.liquidaciones_ayc_router import (
    router as liquidaciones_ayc_router,
)
from src.modules.liquidaciones.presentation.liquidaciones_router import (
    router as liquidaciones_router,
)
from src.modules.prestadores.presentation.prestadores_router import (
    router as prestadores_router,
)
from src.modules.preventivos.presentation.preventivos_router import (
    router as preventivos_router,
)
from src.modules.sla.presentation.pendientes_router import router as sla_pendientes_router
from src.modules.sla.presentation.sla_router import router as sla_router
from src.modules.turnos.presentation.casillas_router import router as turnos_casillas_router
from src.modules.turnos.presentation.grilla_variantes_router import (
    router as turnos_grilla_variantes_router,
)
from src.modules.turnos.presentation.intercambios_router import (
    router as turnos_intercambios_router,
)
from src.modules.turnos.presentation.overrides_router import (
    router as turnos_overrides_router,
)
from src.modules.turnos.presentation.slots_router import router as turnos_slots_router
from src.modules.turnos.presentation.turnos_router import router as turnos_router
from src.modules.vacaciones.presentation.auditoria_router import (
    router as vacaciones_auditoria_router,
)
from src.modules.vacaciones.presentation.ausencias_router import (
    router as vacaciones_ausencias_router,
)
from src.modules.vacaciones.presentation.catalogos_router import (
    router as vacaciones_catalogos_router,
)
from src.modules.vacaciones.presentation.ciclos_router import (
    router as vacaciones_ciclos_router,
)
from src.modules.vacaciones.presentation.dashboard_router import (
    router as vacaciones_dashboard_router,
)
from src.modules.vacaciones.presentation.empleados_router import (
    router as vacaciones_empleados_router,
)
from src.modules.vacaciones.presentation.feriados_router import (
    router as vacaciones_feriados_router,
)
from src.modules.vacaciones.presentation.reportes_router import (
    router as vacaciones_reportes_router,
)
from src.modules.vacaciones.presentation.solicitudes_router import (
    router as vacaciones_solicitudes_router,
)
from src.modules.wati.presentation.pendientes_router import router as wati_pendientes_router
from src.shared.presentation.health.router import router as health_router

# Orden de registro = orden de matching de rutas en FastAPI; no reordenar sin
# revisar catch-alls (ver nota sobre liquidaciones).
ROUTERS: tuple[APIRouter, ...] = (
    health_router,
    auth_router,
    admin_permissions_router,
    admin_users_router,
    route_visits_router,
    dashboard_prefs_router,
    contadores_tools_router,
    ftp_clients_router,
    clientes_nuevos_router,
    sds_router,
    ers_router,
    equipos_sin_real_router,
    anexos_pendientes_router,
    calendario_router,
    insumos_customers_router,
    insumos_requests_router,
    insumos_audit_router,
    insumos_devices_router,
    insumos_statistics_router,
    insumos_mail_log_router,
    insumos_config_router,
    insumos_new_devices_router,
    insumos_offline_devices_router,
    insumos_alerts_router,
    insumos_health_router,
    turnos_router,
    turnos_casillas_router,
    turnos_slots_router,
    turnos_overrides_router,
    turnos_grilla_variantes_router,
    turnos_intercambios_router,
    sla_router,
    sla_pendientes_router,
    prestadores_router,
    preventivos_router,
    # config_router va ANTES: sus rutas son todas literales (/tarifarios, /spsts,
    # /tabla-km, ...), mientras que liquidaciones_router tiene un catch-all
    # GET/DELETE/PATCH /{liquidacion_id} que, registrado primero, interceptaba esos
    # segmentos como si fueran un UUID (422 en vez de la respuesta real).
    liquidaciones_config_router,
    liquidaciones_alertas_router,
    liquidaciones_ayc_router,
    liquidaciones_router,
    vacaciones_empleados_router,
    vacaciones_catalogos_router,
    vacaciones_feriados_router,
    vacaciones_solicitudes_router,
    vacaciones_dashboard_router,
    vacaciones_ciclos_router,
    vacaciones_ausencias_router,
    vacaciones_auditoria_router,
    vacaciones_reportes_router,
    wati_pendientes_router,
    pi_analysis_router,
    pi_cpmd_router,
    pi_error_codes_router,
    pi_sds_router,
    pi_saved_analyses_router,
)
