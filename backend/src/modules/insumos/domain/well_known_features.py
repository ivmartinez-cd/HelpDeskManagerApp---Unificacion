"""Funciones (pantallas) de Insumos concedibles por usuario (ADR-032).
Sembradas en `module_feature`; se exigen con `require_feature` y en el
frontend por el mapa de rutas y el submenú de la barra lateral."""

from src.shared.domain.value_objects.feature_key import FeatureKey

# Apartado "Administración" del submenú: Clientes, Configuración y Estadísticas.
# Sin esta función un operador con `insumos.view` sigue viendo Solicitudes,
# Historial y Equipos, pero no puede tocar clientes, parámetros ni estadísticas.
ADMINISTRACION = FeatureKey("insumos-administracion")
