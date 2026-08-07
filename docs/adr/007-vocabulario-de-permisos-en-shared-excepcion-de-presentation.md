# ADR-007: Vocabulario de permisos en `shared/`, excepción documentada para `require_permission`

## Estado: Aceptado

## Contexto

`ARCHITECTURE_GUIDE.md` §2 exige que ningún módulo de negocio importe `domain`/`application`
de otro módulo — solo pueden depender de `shared/`. Hasta que existió un solo módulo real
(`auth`), esta regla nunca se puso a prueba: `ModuleKey`, `ActionKey`, `Permission` y el
mecanismo `require_permission`/`get_current_identity` vivían enteros dentro de `auth`, porque
no había ningún otro módulo que necesitara declarar sus propios permisos.

Al empezar a portar el segundo módulo real (Contadores, ver `INTEGRACION_APPS_PLAN.md` Fase 3)
apareció la necesidad real: su router necesita poder escribir
`Permission(ModuleKey("contadores"), ActionKey("export"))` y protegerse con
`Depends(require_permission(...))`, sin que eso implique que `contadores` dependa del dominio
de `auth`.

Se evaluaron tres opciones:

1. **Mover todo el mecanismo de identidad a `shared/`** (`get_current_identity`,
   `GetCurrentIdentity`, los repositorios de sesión/usuario/permisos, el generador de
   tokens). Es lo más "puro", pero el costo real es alto: mueve la maquinaria de
   verificación de sesión/JWT — la parte más sensible de `auth`, con 61 tests ya pasando —
   fuera de su módulo, sin necesidad real (nadie más *emite* sesiones, solo las *verifican*).
2. **No mover nada**, dejar que `contadores` importe directo de `auth.domain` — rompe la
   regla de independencia sin dejar rastro de que fue una decisión consciente.
3. **Híbrido**: mover solo lo que es vocabulario puro y no tiene dependencias hacia el resto
   de `auth` (`ModuleKey`, `ActionKey`, `Permission`) a `shared/domain/value_objects/`, y
   dejar `require_permission`/`get_current_identity` en `auth.presentation`, con una
   excepción de import-linter **acotada y documentada** que solo habilita
   `contadores.presentation → auth.presentation` — nunca `contadores.domain` ni
   `contadores.application`.

## Decisión

Opción 3. `ModuleKey`, `ActionKey`, `Permission` (y sus errores de validación
`InvalidModuleKeyError`/`InvalidActionKeyError`) pasan a `shared/domain/`. `PermissionSet`
queda en `auth` (es "los permisos que tiene un usuario", un concepto propio de auth, no
vocabulario transversal).

`require_permission` y `get_current_identity` **no se mueven** — verificar la sesión/JWT
sigue siendo responsabilidad exclusiva de `auth`, que es quien también las emite (login,
refresh). Cualquier módulo de negocio puede importar
`src.modules.auth.presentation.dependencies.permissions.require_permission` desde su propia
capa `presentation` para proteger sus endpoints — es la única dirección de dependencia
permitida entre módulos de negocio y `auth`, y solo en esa capa.

Esto se refuerza con dos contratos de `import-linter` (`.importlinter`), en vez de uno solo
de independencia total:

- `contadores.{domain,application}` no puede importar nada de `auth` — la parte que
  realmente importa para poder testear/reemplazar el módulo de forma aislada.
- `auth` no puede importar nada de `contadores` — la excepción es de una sola dirección.

La capa `presentation` de `contadores` queda deliberadamente fuera del primer contrato: ahí
es donde vive el único acoplamiento permitido, y es explícito (esta ADR), no accidental.

## Consecuencias

- Positivas: el núcleo de negocio de cada módulo (`domain`/`application`) queda 100%
  independiente y testeable sin `auth` — que es lo que de verdad protege el `import-linter`.
  No se tocó ninguna línea de la maquinaria de sesión/token de `auth` (0 riesgo sobre sus 61
  tests). Agregar un tercer módulo de negocio repite el mismo patrón sin fricción.
- Negativas: la independencia entre módulos de negocio y `auth` no es total — la capa
  `presentation` de cada módulo de negocio sigue importando `require_permission` de `auth`.
  Si en el futuro se necesita reemplazar o extraer `auth` a un servicio separado, ese
  acoplamiento puntual (no el de dominio) es el que habría que resolver primero.
- Revisar esta decisión si aparece un tercer o cuarto caso de uso que necesite algo más de
  `auth` que `require_permission` — sería señal de que el mecanismo de identidad sí necesita
  moverse a `shared/` (opción 1, descartada acá por costo/beneficio en este momento).
