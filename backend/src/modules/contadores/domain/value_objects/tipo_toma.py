"""Catálogo de tipos de toma de Contadores (espejo de `Tipo_Toma` de SiGes).
Centraliza acá lo que el legacy tenía en `Models/TipoToma.cs` — evita
"magic numbers" repartidos por el módulo. `TIPOS_REALES` es la MISMA lista
que usa `GetGrillaEstimacion.sql`/`GetHistorialEquipo.sql` en sus cláusulas
IN; si se agrega un canal de captura nuevo hay que tocar ambos lados."""

TIPOS_REALES = frozenset({1, 2, 3, 6, 7, 9, 10, 12, 15, 17, 20, 21, 22, 23})

CONTADOR_INICIAL = 8
CONTADOR_FINAL = 13
CONTADOR_REINICIAL = 16
ST = 4
ESTIMADO = 14
PROMEDIO_INSTALACION = 19

_INICIALES_FINALES = frozenset({CONTADOR_INICIAL, CONTADOR_FINAL, CONTADOR_REINICIAL})


def es_real(id_tipo_toma: int) -> bool:
    return id_tipo_toma in TIPOS_REALES


def es_inicial_final(id_tipo_toma: int) -> bool:
    return id_tipo_toma in _INICIALES_FINALES
