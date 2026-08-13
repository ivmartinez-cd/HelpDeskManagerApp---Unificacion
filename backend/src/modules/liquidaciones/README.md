# liquidaciones

Fase 3 de `INTEGRACION_APPS_PLAN.md` en curso (migración de Liquidacion-Prestadores).
Caracterización del legacy en `LIQUIDACION_PRESTADORES_CARACTERIZACION.md` (raíz del
repo) — leerla antes de escribir código acá, tiene el catálogo real de reglas
ALT001-009, el modelo de datos completo y los riesgos heredados (motor de reglas
híbrido data-driven/hardcodeado, integración WS AyC no mencionada en los docs
funcionales y aún no productiva).

**No confundir con `backend/src/modules/prestadores`** — ese es el catálogo de PST
vinculado a Siges para asignar operador de Canal Directo y filtrar "mis PST" en SLA, sin
relación con el motor de preliquidaciones de este módulo. Ver
`backend/src/modules/prestadores/README.md`.
