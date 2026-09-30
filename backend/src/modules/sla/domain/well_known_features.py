"""Funciones de SLA concedibles por usuario (ADR-032). Sembradas en
`module_feature` por migración."""

from src.shared.domain.value_objects.feature_key import FeatureKey

# Recibir en la campanita los casos de Mesa de Ayuda con una visita de técnico
# en marcha en la misma sucursal (job `aviso_visita_sucursal`).
AVISOS_MESA_AYUDA = FeatureKey("sla-avisos-mesa-ayuda")
