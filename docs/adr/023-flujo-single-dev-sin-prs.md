# ADR-023: Flujo de versionado single-dev, sin PRs ni review

## Estado: Aceptado (2026-08-16)

## Contexto

`ARCHITECTURE_GUIDE.md` §9 exige PRs de ≤400 líneas, al menos 1 reviewer, CI verde
antes de merge y prohíbe mergear el propio PR sin review. La auditoría del
2026-08-14 marcó (hallazgo BAJO) que nada de eso existe como proceso: el repo lo
desarrolla una sola persona, se commitea directo a `main`, no hay CI, y una parte
de los commits supera las 400 líneas (portar un módulo entero de una app legacy es
naturalmente un cambio grande).

Los supuestos de §9 (varios devs, un pipeline, un reviewer disponible) no se dan:
un "PR" acá sería la misma persona aprobándose a sí misma, y el tope de 400 líneas
partiría ports de módulos que se validan como unidad contra datos reales.

## Decisión

Se documenta el flujo real como excepción consciente a §9:

1. **Commits directos a `main`**, atómicos por cambio lógico, con Conventional
   Commits en inglés (esto de §9 se mantiene y se cumple — ver historial).
2. **El reemplazo de "CI verde" son los gates locales obligatorios** de CLAUDE.md,
   corridos antes de cada cierre: `lint-imports`, `ruff`, `mypy`,
   `pytest tests/unit` (backend) y `tsc` + `eslint` (frontend). Un commit que los
   rompa es un bug a arreglar de inmediato (como el caso `4219c59`, corregido en
   `3911709` el mismo día).
3. **El reemplazo de la review es el par de salvaguardas ya vigentes**: la
   verificación e2e manual por módulo (ADR-022) y las pasadas de auditoría
   periódicas contra la guía (`docs/OPTIMIZACION.md`), que revisan el código ya
   mergeado con los mismos criterios que una review.
4. **El tope de 400 líneas no aplica a ports de módulos legacy**; sí se mantiene
   como aspiración para el trabajo incremental posterior.

## Consecuencias

- Positivas: el proceso escrito coincide con el real; la desviación de §9 deja de
  ser violación silenciosa; queda explícito qué mecanismo cubre cada garantía que
  §9 buscaba (calidad → gates; segundo par de ojos → auditoría periódica).
- Negativas: no hay barrera *previa* al merge — un commit roto entra y se detecta
  después (gates o auditoría), no antes. Riesgo aceptado para un solo dev.
- **Cláusula de reversión** (compartida con ADR-022): si se suma un segundo
  desarrollador o aparece CI, §9 vuelve a aplicar en su forma literal — branches,
  PRs con review y pipeline como gate de merge.
