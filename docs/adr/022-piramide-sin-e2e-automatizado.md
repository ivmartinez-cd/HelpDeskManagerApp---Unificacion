# ADR-022: Pirámide de testing sin capa e2e automatizada

## Estado: Aceptado (2026-08-16)

## Contexto

`ARCHITECTURE_GUIDE.md` §7 define la pirámide con un 5–10% de tests e2e (flujos
completos navegador → API → DB) y una cobertura mínima de presentation "60% (e2e)".
La auditoría del 2026-08-14 lo marcó como hallazgo MEDIO: la app tiene tests
unitarios (1382 al día de esta ADR) y de integración (repositorios contra Postgres
real), pero cero e2e automatizado, y dejó la decisión abierta: suite mínima o ADR
que redefina la pirámide.

Lo que hace distinto a este monorepo:

1. **Las integraciones críticas son sistemas productivos vivos.** SDSInsumos sigue
   en producción durante la migración; la DB de dev tiene datos reales; el SMTP es
   real; wsAyC/Siges/Insight/Google son servicios productivos o pagos. Un e2e
   automatizado acá enfrenta un dilema sin salida buena: si mockea esas
   integraciones, no prueba lo que históricamente se rompe (los bugs de esta app
   aparecieron en la integración real, no en la lógica local — diagnóstico ya
   asentado en ADR-016/017); si no las mockea, dispara efectos reales sobre gente
   real (CLAUDE.md prohíbe exactamente eso — incidente 2026-08-12).
2. **Flujo single-dev sin CI.** No hay pipeline donde una suite e2e corra sola con
   entorno efímero; correría a mano contra los mismos contenedores de desarrollo,
   compitiendo con el protocolo que ya existe.
3. **Ya existe una verificación end-to-end, humana y obligatoria.** Cada módulo
   portado se da por terminado solo tras verificarse en el navegador contra los
   contenedores reales (CLAUDE.md: build servido verificado con curl, captura
   visual contra el design handoff, datos reales de la DB sembrada). Es e2e de
   verdad — con el criterio de un humano — ejecutado en el momento de mayor
   riesgo: el cierre de cada módulo.

## Decisión

La pirámide de este monorepo queda redefinida como **unit (mayoría) + integración
(repos contra Postgres real) + verificación e2e manual por módulo**, sin capa e2e
automatizada. La fila "Presentation 60% (e2e)" de §7 se lee como cobertura de la
capa presentation por los tests existentes (74.1% en la última medición) más la
verificación manual documentada, no como suite automatizada pendiente.

**Cláusula de reversión** — esta decisión se revierte y se construye la suite
mínima (Playwright contra los contenedores: login + una pantalla por módulo + los
flujos mutantes críticos en dry-run) si ocurre cualquiera de estas dos cosas:

1. Aparece un **segundo** bug tipo `CorregirPin` (2026-08-16): endpoint roto en
   runtime con todos los gates en verde. El primero se resolvió con tests
   unitarios del use case; el segundo probaría que esa red no alcanza.
2. El proyecto suma CI o un segundo desarrollador — los supuestos 2 y 3 del
   contexto dejan de valer.

## Consecuencias

- Positivas: cero costo de construir y mantener la capa de tests más frágil y
  lenta; ningún riesgo de que una suite automatizada dispare efectos reales sobre
  los sistemas productivos; la desviación de §7 deja de ser violación silenciosa.
- Negativas: las regresiones de cableado entre capas (rutas, cookies, proxy del
  frontend) solo se detectan en la verificación manual o en uso real; el criterio
  de "flujo crítico verificado" vive en la disciplina del protocolo de CLAUDE.md,
  no en código ejecutable.
- La cláusula de reversión es parte del contrato de esta ADR: no cumplirla ante su
  disparador convierte la desviación de nuevo en violación.

## Addendum 2026-08-23: decisión cerrada sobre e2e real y jobs de fondo

1. **No se construye una suite e2e real (navegador → API → DB) ahora.** La red elegida es:
   `make check` (unit + integración de repos contra Postgres real + tests de routers por HTTP
   con la app real) en cada push; smoke Playwright de UI con backend mock en el pre-push
   cuando hay cambios de frontend; suite Playwright completa a mano al cerrar cambios de API
   consumida por el front; y la verificación manual en el navegador contra los contenedores
   reales que ya forma parte del cierre de cada bloque (capturas con usuario e2e temporal,
   como se hizo en el rediseño de Inicio). La cláusula de reversión de arriba sigue siendo el
   único disparador para cambiar esto.
2. **`*/presentation/background_jobs.py` queda sin cobertura a propósito.** La regla de
   CLAUDE.md prohíbe ejecutar jobs de fondo en dev (mandan mails y escriben contra SOAP/
   Insight/wsAyC reales); la lógica de negocio de cada job vive en use cases que sí tienen
   tests, y el archivo de jobs es solo scheduling. No es un pendiente de cobertura.
