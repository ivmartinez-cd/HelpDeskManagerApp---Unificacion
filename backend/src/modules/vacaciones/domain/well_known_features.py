"""Funciones (pantallas/cards) de Gestión de Personal concedibles por usuario
(ADR-032). Solicitudes y Aprobaciones siguen siendo acciones (create/approve)."""

from src.shared.domain.value_objects.feature_key import FeatureKey

DASHBOARD = FeatureKey("vacaciones-dashboard")
ASISTENCIAS = FeatureKey("vacaciones-asistencias")
GESTION_HUMANA = FeatureKey("vacaciones-gestion-humana")
REPORTES = FeatureKey("vacaciones-reportes")
AUDITORIA = FeatureKey("vacaciones-auditoria")
CONFIGURACION = FeatureKey("vacaciones-configuracion")
CARD_EQUIPO = FeatureKey("vacaciones-card-equipo")
