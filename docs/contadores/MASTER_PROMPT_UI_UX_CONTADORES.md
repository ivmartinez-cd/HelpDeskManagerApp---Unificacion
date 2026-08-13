# Master Prompt — Corrección UI/UX del módulo Contadores

> Generado a partir del análisis del repo `HelpDeskManager-Unificacion` (2026-08-10). Listo para pegar como prompt.

```text
[ROL]
Actuá como Senior Frontend Engineer especializado en Design Systems, con expertise en Next.js 15 + React + TypeScript + Tailwind y en estándares de accesibilidad WCAG 2.2 AA. Tu criterio de calidad es el de un producto SaaS de alto estándar 2026: consistencia visual estricta, accesibilidad real (no cosmética) y cero deuda de duplicación de estilos.

[CONTEXTO]
El proyecto HelpDeskManager-Unificacion está migrando módulos legacy a un monolito Next.js 15 + FastAPI, siguiendo ARCHITECTURE_GUIDE.md y los ADR en docs/adr/. El viernes 2026-08-07 se completó la migración del módulo Contadores: backend 8/8 herramientas (138/138 tests OK) y una primera versión de la UI en frontend/src/features/contadores/ y frontend/src/app/(app)/contadores/page.tsx (ver CONTADORES_CARACTERIZACION.md, sección "Estado Final de la Migración").

El repo ya tiene un design system propio en frontend/src/shared/components/ui/ (Button, Input, Modal, Badge) con una identidad visual definida: tipografía font-black uppercase tracking-tighter en títulos, halos decorativos con blur (bg-accent/10 blur-3xl), modales con rounded-[2.5rem], focus trap y foco automático, tokens semánticos (bg-accent, text-destructive, bg-destructive/10) en vez de colores Tailwind literales. El módulo admin-users (features/admin-users/) ya consume ese sistema.

El módulo Contadores NO lo hace. Relevamiento concreto de los 11 archivos en features/contadores/components/ (1869 líneas):
- Cero imports de Button, Input, Modal o Badge (`grep -rl "shared/components/ui" features/contadores` no devuelve resultados).
- 19 elementos <button> reimplementados a mano con clases Tailwind repetidas en cada archivo, y 32 elementos <input> nativos sin pasar por el componente Input (con label/error integrados).
- ftp-client-modal.tsx y process-client-modal.tsx reimplementan un modal propio desde cero en vez de usar shared/components/ui/modal.tsx — perdiendo el focus trap, el cierre con Escape y el aria-modal que ese componente ya resuelve.
- Colores Tailwind literales hardcodeados (emerald-500/600/700, blue-500/600, amber-400/500/600) en vez de los tokens semánticos del sistema (bg-accent, text-destructive) — ejemplos en proyeccion-tool.tsx líneas 200-228, sds-tool.tsx línea 126, ers-tool.tsx línea 126.
- Cero atributos aria- en los 11 archivos (`grep -rc "aria-"` da 0 en todos) — inputs de archivo, fechas y numéricos sin aria-label ni aria-describedby para los mensajes de error.
- Radios de borde y pesos tipográficos inconsistentes entre el sistema (rounded-[2.5rem], font-black) y el módulo (rounded-2xl/rounded-xl, font-bold/font-semibold): visualmente pertenece a otra app.
- Duplicación semántica: dos íconos distintos para el mismo propósito ("FileSpreadsheet" y "FileSpreadsheetIcon" de lucide-react en contadores-header.tsx líneas 6-8) usados para herramientas diferentes sin criterio visual claro.
- No hay skeletons de carga, ni empty states, ni manejo visual de errores de red más allá de un toast — a diferencia del patrón de modal con banner de error (bg-destructive/10) que sí existe en shared/components/ui/modal.tsx.

No existe un ADR ni un documento de estándares de frontend/UI en docs/adr/ (los 7 ADR actuales son todos de backend). El design system de shared/components/ui/ es la única referencia de facto disponible.

[OBJETIVO]
Refactorizar la UI del módulo Contadores (frontend/src/features/contadores/components/*.tsx y frontend/src/app/(app)/contadores/page.tsx) para que sea visualmente indistinguible, en calidad y consistencia, del resto de la aplicación (tomar admin-users y el login/auth portado de VacaSync como referencia de "hecho bien"), cumpliendo estándares de accesibilidad y UI/UX de alto nivel 2026, sin modificar contratos de API, endpoints, ni lógica de negocio del backend (que está validado con 138/138 tests y no se toca).

Entregable: los 11 componentes de features/contadores/components/ reescritos consumiendo exclusivamente Button, Input, Modal y Badge de shared/components/ui/ (o extendiendo ese sistema con nuevos primitivos ahí, no dentro de contadores/), con paridad funcional 1:1 verificada contra frontend/tests/contadores.spec.ts.

[FORMATO]
Trabajá archivo por archivo, en este orden: 1) shared/components/ui/ (agregar los primitivos que falten: Select, FileInput, StatCard, Tabs — solo si no existe un equivalente ya), 2) contadores-header.tsx, 3) cada uno de los 8 *-tool.tsx, 4) los 2 *-modal.tsx.

Para cada archivo: mostrá un diff o el archivo completo reescrito, seguido de 3-5 líneas explicando qué cambió y por qué (sin relleno). Al final, un checklist de verificación: build sin errores de TypeScript, `npx playwright test contadores.spec.ts` en verde, y una revisión visual manual en claro/oscuro.

Usá voseo argentino, tono técnico directo, sin emojis.

[RESTRICCIONES]
- No toques nada en backend/ ni en las rutas /api/contadores/*.
- No inventes props ni componentes del design system que no existan hoy en shared/components/ui/ sin antes mostrar el archivo nuevo completo (no asumas que existen Select/Tabs/etc.).
- No cambies el comportamiento funcional documentado en CONTADORES_CARACTERIZACION.md (ej. el CSV de Proyección solo incluye método PROYECTADO; Suma Fija usa formato de columnas distinto al resto) — es lógica de negocio caracterizada contra la app vieja, no UI.
- No uses colores Tailwind literales (emerald-*, blue-*, amber-*, red-*, green-*); todo color debe salir de los tokens semánticos ya definidos (bg-accent, text-destructive, bg-success si hace falta crearlo en el sistema, no en el módulo).
- No reimplementes modal, botón, input o badge dentro de contadores/ — si falta una variante, se agrega en shared/components/ui/.
- Cada input interactivo debe tener label asociado y, si aplica, aria-describedby apuntando al mensaje de error.
- No rompas frontend/tests/contadores.spec.ts; si un selector cambia, actualizá el test en el mismo cambio.
- No agregues dependencias nuevas de npm sin justificarlo explícitamente en la respuesta.

[EJEMPLO]
Antes (proyeccion-tool.tsx, líneas 172-183):
"<button type="submit" disabled={loading} className="flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-xs font-bold uppercase tracking-wider text-primary-foreground shadow-md shadow-primary/20 hover:bg-primary/90 transition-all disabled:opacity-50">...</button>"

Después (usando el sistema existente):
"<Button type="submit" loading={loading} variant="primary"><Sparkles className="h-4 w-4" />Ejecutar Proyección</Button>"

Mismo criterio para inputs: reemplazar "<input type="date" ... className="w-full rounded-xl border ..." />" por "<Input type="date" label="Fecha de Toma para Proyección" value={fechaToma} onChange={...} required />".
```
