# ADR-016: Deuda aceptada de tamaño de funciones (§4) en el módulo liquidaciones

## Estado: Aceptado (2026-08-13)

## Contexto

La validación adversarial del pipeline
(`docs/liquidaciones/VALIDACION_PIPELINE_LIQUIDACIONES_2026-08-13.md`, hallazgo H-7)
midió con AST el cumplimiento de los límites de `ARCHITECTURE_GUIDE.md` §4 en
`src/modules/liquidaciones`:

- Archivos ≤300: 1 violación (`presentation/_liq_csv.py`, 302 líneas).
- Clases ≤200: 0 violaciones.
- Funciones ≤20: ~40 violaciones, casi todas entre 21 y 37 líneas de span físico
  (incluyendo firma multilínea y docstring), concentradas en use cases de sync
  Siges, repositorios SQLAlchemy (create/update con muchas columnas), schemas
  `from_dto` y helpers de importación.

El módulo está portado, verificado contra datos reales y en uso por la Team
Leader; los tests que lo protegen son mayormente de caracterización.

## Decisión

1. **La violación de archivo se corrige** (mismo día): `_liq_csv.py` se separa en
   `_liq_csv.py` (imports) y `_liq_csv_export.py` (exports), descomponiendo de paso
   sus dos funciones más largas (51 y 44 líneas) en helpers por responsabilidad.
2. **Las funciones de 21–37 líneas restantes se aceptan como deuda documentada, no
   se refactorizan en bloque.** Razones:
   - Son mayormente firmas keyword-only de muchas columnas (repos, schemas) y
     docstrings — el span físico sobreestima la complejidad; ninguna supera ~25
     sentencias.
   - Refactorizar ~40 funciones verificadas contra el contenedor real solo para
     satisfacer un conteo de líneas agrega riesgo de regresión y ruido de review
     sin reducir complejidad real (el historial del módulo muestra que los bugs
     aparecieron en la integración real, no en unidades largas).
3. **El límite §4 sigue vigente para todo código nuevo del módulo** — esta
   excepción cubre solo el inventario existente al 2026-08-13 (listado en el
   informe de validación). Cualquier función nueva o reescrita entra en ≤20.

## Consecuencias

- Queda un registro explícito de la desviación (una excepción sin ADR es una
  violación, per CLAUDE.md).
- Si una de estas funciones se toca por otro motivo, se aprovecha ese cambio para
  bajarla del límite; no se abre un workstream de refactor dedicado.
