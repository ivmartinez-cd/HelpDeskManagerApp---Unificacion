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
# Calendario con los eventos de todos los operadores (y el filtro por operador);
# sin esta función cada uno ve solo los suyos y los que cubre.
CALENDARIO_TODOS = FeatureKey("contadores-calendario-todos")
# Operar la Proyección (panel de candidatos: elegir P/L, forzar método,
# aceptar, marcar pendiente; y exportar el CSV a SiGes) sin necesitar
# `contadores.manage` completo (que además da la gestión de recesos). Ver
# `require_feature_or_permission`.
PROYECCION_OPERAR = FeatureKey("contadores-proyeccion-operar")
