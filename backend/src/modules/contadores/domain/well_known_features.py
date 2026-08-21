"""Funciones (pantallas/cards) de Contadores concedibles por usuario (ADR-032).
Sembradas en `module_feature`; se exigen con `require_feature` / `tiene_feature`
y en el frontend por el mapa de rutas y el registro de cards de Inicio."""

from src.shared.domain.value_objects.feature_key import FeatureKey

COBERTURAS = FeatureKey("contadores-coberturas")
ANEXOS = FeatureKey("contadores-anexos")
CLIENTES_NUEVOS = FeatureKey("contadores-clientes-nuevos")
# "Sin contador real" completo; sin esta función se ve solo lo de los clientes
# asignados al usuario (cruce por nombre de operador, ADR-009).
SIN_REAL_TODOS = FeatureKey("contadores-sin-real-todos")
CARD_OPERADORES = FeatureKey("contadores-card-operadores")
