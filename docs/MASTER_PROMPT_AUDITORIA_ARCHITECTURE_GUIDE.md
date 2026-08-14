# Master Prompt — Auditoría de cumplimiento de ARCHITECTURE_GUIDE.md en toda la app

Verificar, con evidencia medible y no "a ojo", en qué grado **toda** la app HelpDeskManagerApp---Unificacion
(backend + frontend, todos los módulos) cumple `docs/ARCHITECTURE_GUIDE.md`. No es una auditoría de un
módulo: es un barrido transversal de las 12 secciones de la guía sobre los ~10 módulos backend y las
features del frontend, produciendo una matriz de cumplimiento por sección×módulo y hallazgos priorizados.

Generado el 2026-08-13. La guía es regla dura del repo (CLAUDE.md: "todo código nuevo tiene que cumplirla
mientras se escribe"), y las desviaciones conscientes se documentan como ADR — una desviación sin ADR es
una violación, no una decisión (ver ADR-007 y ADR-016 como precedentes de excepciones documentadas).

---

```text
[ROL]
Actuá como auditor/arquitecto senior ESCÉPTICO del monorepo HelpDeskManagerApp---Unificacion (FastAPI +
SQLAlchemy async + Alembic + Next.js App Router, backend módulo→capa domain/application/infrastructure/
presentation). Tu tarea es medir el cumplimiento de `docs/ARCHITECTURE_GUIDE.md` en TODA la app, no
arreglar nada. Cada afirmación va respaldada por el comando exacto y su salida real; medís con
herramientas (lint-imports, ruff, mypy, AST, grep, cobertura), no por lectura impresionista. Cero
alucinaciones: si un número no se midió, no se afirma. Distinguís violación real de estilo opinable, y
violación de desviación YA documentada en un ADR (esa no es hallazgo, es decisión). Respondés en español
de Argentina, directo, sin cortesías. NO cambiás código en esta pasada — reportás.

[CONTEXTO]
Alcance: TODO el repo, no un módulo.
- Backend `backend/src/modules/`: auth, contadores, insumos, liquidaciones, parque_impresoras,
  prestadores, sla, stc, turnos, vacaciones — más `backend/src/shared/`. Cada módulo tiene sus capas
  domain/application/infrastructure/presentation.
- Frontend `frontend/src/`: features/ (admin-permissions, admin-users, auth, coberturas, contadores,
  home, insumos, liquidaciones, prestadores, sla, turnos, vacaciones), shared/, services/, app/.
- ADRs existentes en `backend/docs/adr/` (001–016) documentan desviaciones ya aceptadas — leerlos ANTES
  de reportar, para no marcar como violación algo que ya tiene ADR (ej. ADR-016: deuda de funciones §4
  de 21–37 líneas en liquidaciones; ADR-007: vocabulario de permisos en shared).

La guía (`docs/ARCHITECTURE_GUIDE.md`) y cómo verificar cada sección con herramienta, no a ojo:
- §2/§3 Estructura y capas (LA MÁS IMPORTANTE, no opinable): dependencias hacia adentro
  (Presentation→Application→Domain←Infrastructure) y ningún módulo importa domain/application de otro
  (solo `shared/`). Se verifica con `uv run lint-imports` (import-linter) — es la única forma confiable,
  no revisar imports a mano. Reportar contratos KEPT/BROKEN.
- §4 Convenciones y tamaños: función ≤20 líneas, clase ≤200, archivo ≤300, ≤3 parámetros, anidamiento
  ≤3. Medir con un script AST sobre `backend/src` (span físico) — no estimar. Nomenclatura (PascalCase
  tipos, snake_case archivos py / kebab-case ts, SCREAMING_SNAKE_CASE constantes). Patrones prohibidos:
  magic numbers, doble negación, efectos secundarios ocultos, God Objects.
- §5 Dependencias: toda librería externa aislada detrás de una interfaz propia (Adapter); el dominio no
  importa librerías de terceros. Verificar que zeep/pyodbc/pandas/httpx/etc. no aparezcan en `domain/`
  ni `application/` (grep de imports por capa + lint-imports).
- §6 Manejo de errores: ningún `except Exception` que silencie; logging en el punto donde se maneja, con
  contexto; errores de infra envueltos (`ExternalServiceError`); jerarquía `AppError`. Grep de
  `except Exception`, `except:` y `pass`/`continue` sin log; revisar cada hit.
- §7 Testing: pirámide y cobertura mínima (domain 90%, application 85%, infra 70%, presentation 60%).
  Correr `pytest --cov` por capa/módulo y comparar contra esos mínimos; si la cobertura no está
  configurada, decirlo y reportar al menos el conteo de tests por módulo.
- §8 Seguridad: input validado en el borde; auth vs authz separadas; queries parametrizadas (sin
  concatenación de strings con input); sin secretos en el código. Grep de f-strings/`%`/`+` en SQL, de
  literales tipo password/token/key, y verificar que los endpoints usan `require_permission`/identidad.
- §9 Control de versiones: Conventional Commits en el historial; PRs ≤400 líneas (informar si el
  historial reciente lo respeta, sin bloquear).
- §10 Documentación: decisiones arquitectónicas con ADR; README por proyecto. Verificar que las
  desviaciones detectadas en §4/§6/etc. tengan (o no) su ADR.
- §11 Rendimiento: paginación obligatoria en todo endpoint que devuelve colección (envelope `Page[T]`);
  N+1 prohibidas; índices revisados; caching con expiración explícita. Grep de endpoints que devuelven
  `list[...]` sin `Page[T]`; buscar loops con query adentro (N+1).
- §12 Checklist por PR y Apéndice de anti-patrones (God Object, Primitive Obsession, Shotgun Surgery,
  Leaky Abstractions, Anemic Domain Model, Hardcoded Configuration): usarlos como grilla de smells.

Infra para correr: contenedor `helpdesk-manager-backend` (gates de Python), frontend
`helpdesk-manager-frontend` (`tsc`, `eslint`). `DISABLE_BACKGROUND_JOBS=true` antes de levantar el
backend. Postgres `helpdesk-db` (`localhost:5439`), db-test `localhost:5440`.

[OBJETIVO]
Entregar un informe de cumplimiento con matriz sección×módulo y hallazgos priorizados. Fases:

FASE 1 — Medición global con herramientas (una pasada, números duros):
  - `uv run lint-imports` (§2/§3) → contratos KEPT/BROKEN.
  - `uv run ruff check src tests` y `uv run mypy src` → cero errores esperado; reportar cualquiera.
  - Script AST §4 sobre `backend/src`: listar TODA función >20, clase >200, archivo >300, firma >3
    params, anidamiento >3 — agrupado por módulo, con archivo:línea y el número real.
  - Frontend: `tsc` + `eslint` (incluida la regla `react-hooks/set-state-in-effect` que ya mordió).
  - Grep §5 (imports de terceros en domain/application), §6 (`except Exception`/`except:`/`pass`),
    §8 (SQL por concatenación, posibles secretos), §11 (endpoints `list[...]` sin `Page[T]`).
  Entregable: tabla de números por módulo.

FASE 2 — Cumplimiento por sección de la guía (§1 a §12):
  Para cada sección, veredicto CUMPLE / CUMPLE-CON-DESVIACIONES-DOCUMENTADAS / NO-CUMPLE, con la
  evidencia de la Fase 1 y, donde haga falta, lectura dirigida. Cada desviación se cruza contra los ADR:
  si tiene ADR → no es hallazgo; si no → es hallazgo.

FASE 3 — Matriz sección×módulo:
  Grilla con las 10+shared del backend (y una fila frontend) × las secciones medibles (§2/3, §4, §5, §6,
  §7, §8, §11), cada celda VERDE/AMARILLO/ROJO con el dato que la respalda. Identificar los módulos con
  más deuda y los patrones recurrentes (mismo smell repetido en N módulos = problema sistémico, no local).

FASE 4 — Hallazgos priorizados y recomendación:
  Lista por severidad (crítico/alto/medio/bajo), cada uno con sección de la guía violada, archivo:línea o
  comando, impacto y si amerita fix inmediato, ADR de excepción, o backlog. Cerrar con: ¿la app cumple la
  guía hoy? (sí / sí con deuda acotada y documentada / no), y los 3–5 focos de mayor retorno.

[FORMATO]
- Informe en español de Argentina, directo, sin relleno, como markdown en
  `docs/AUDITORIA_ARCHITECTURE_GUIDE_<fecha>.md` (raíz de docs, es app-wide).
- Números REALES de esta corrida con el comando que los produjo; si algo no se pudo medir (cobertura no
  configurada, etc.), decirlo explícito, no rellenar.
- Matriz sección×módulo como tabla. Hallazgos como tabla (sev · sección · módulo · evidencia · impacto ·
  ¿ADR? · acción sugerida).
- Distinguir violación real de estilo opinable, y violación de desviación ya cubierta por ADR.
- NO cambiar código. Es auditoría, no intervención.

[RESTRICCIONES]
Operativas (CLAUDE.md):
- `DISABLE_BACKGROUND_JOBS=true` aplicado de verdad antes de levantar el backend (`printenv` + log sin
  `background_jobs: N job(s) iniciados`). Sin hot reload: si hiciera falta reconstruir para medir, hacerlo
  y verificar. Solo lectura contra fuentes externas y contra la DB; no tocar la app legacy.
- No correr procesos que escriban datos reales (sync WS completo, jobs) como parte de la auditoría.

De método (para que la auditoría valga):
- Medir, no opinar: §2/§3 se decide por lint-imports, §4 por AST, no por lectura. "Se ve prolijo" no es
  evidencia de cumplimiento; "0 contratos BROKEN" sí.
- Toda desviación se cruza contra los ADR 001–016 ANTES de reportarla: lo ya documentado es decisión, no
  hallazgo (pero SÍ verificar que el ADR realmente cubre lo que se encontró, no que solo suene parecido).
- Distinguir hallazgo confirmado (con evidencia) de sospecha (sin poder medir), rotularlos distinto.
- No inflar: un umbral por 1 línea (función de 21) y un God Object de 400 líneas no tienen la misma
  severidad; priorizar por impacto real (§2/§3 y §6 pesan más que un archivo de 305 líneas).

[EJEMPLO]
Fila esperada de la matriz sección×módulo:

  | Módulo | §2/3 capas | §4 tamaños | §6 errores | §11 paginación |
  |--------|-----------|-----------|-----------|----------------|
  | liquidaciones | VERDE (lint-imports 19/19) | AMARILLO (N funcs 21–37 líneas, cubierto por ADR-016) | VERDE | VERDE (Page[T] en todos los list) |

Fila esperada de la tabla de hallazgos:

  | Sev | Sección | Módulo | Evidencia | Impacto | ¿ADR? | Acción |
  |-----|---------|--------|-----------|---------|-------|--------|
  | ALTO | §6 errores | <módulo> | `<archivo>:NN` `except Exception: pass` sin log | un fallo se traga sin rastro | No | fix |

Encabezado esperado del veredicto:

  ¿La app cumple ARCHITECTURE_GUIDE.md hoy? SÍ CON DEUDA ACOTADA — capas 100% (lint-imports N/N),
  ruff/mypy limpios; deuda concentrada en §4 (M funciones >20 líneas en K módulos, X cubiertas por ADR)
  y J `except Exception` a revisar en §6. Focos de mayor retorno: <1..5>.
```

---

## Notas de contexto para quien use este prompt (fuera del prompt en sí)

- **La sección más importante y la más objetiva es §2/§3 (capas y dependencias).** Se decide con
  `lint-imports`, que es binario: o los contratos están KEPT o hay imports cruzados entre módulos o hacia
  afuera. Si eso está en verde en toda la app, el esqueleto arquitectónico está sano aunque haya deuda
  cosmética; si hay contratos BROKEN, es lo primero a reportar por encima de cualquier función larga.
- **§4 (tamaños) es donde casi siempre aparece la deuda real y hay que medirlo con AST, no a ojo.** El
  precedente ya existe: en liquidaciones la deuda de funciones de 21–37 líneas se aceptó y documentó en
  ADR-016. La auditoría tiene que separar tres cosas: lo que cumple, lo que excede pero YA tiene ADR (no
  es hallazgo), y lo que excede SIN ADR (sí es hallazgo). Confundirlas infla el informe y le quita valor.
- **El patrón sistémico importa más que el hit puntual.** Un `except Exception` silencioso en un módulo
  es un bug; el mismo patrón repetido en seis módulos es un problema de práctica que amerita una decisión
  transversal (o un lint que lo prohíba), no seis tickets sueltos. Por eso la Fase 3 busca lo recurrente.
- **Es auditoría, no arreglo.** El objetivo es saber dónde está parada la app respecto de su propia guía,
  con números. Los fixes —y qué se acepta como ADR vs qué se corrige— son una decisión posterior, con su
  propio prompt, priorizada por lo que este informe encuentre.
