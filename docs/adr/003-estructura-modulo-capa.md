# ADR-003: Estructura módulo → capa (desviación explícita de ARCHITECTURE_GUIDE.md §2)

## Estado: Aceptado

## Contexto

`ARCHITECTURE_GUIDE.md` §2 documenta una estructura backend **capa → módulo**
(`src/domain/`, `src/application/`, `src/infrastructure/`, `src/presentation/` en el
primer nivel, con subcarpetas por dominio dentro de cada capa). `INTEGRACION_APPS_PLAN.md`
§2 refuerza esa misma notación (`domain/insumos/`, `domain/liquidaciones/`, etc.).

Esa estructura fue pensada para una aplicación de un solo dominio. Este proyecto es un
monolito modular con 6 dominios de negocio bien delimitados (auth, insumos, liquidaciones,
vacaciones, parque de impresoras, stc). Con capa → módulo, una feature contenida en un solo
dominio (ej. "agregar un campo al perfil de usuario") obliga a tocar 4 árboles de
directorios distintos (`domain/auth/`, `application/auth/`, `infrastructure/auth/`,
`presentation/auth/`) — es el anti-patrón *Shotgun Surgery* que el propio Apéndice de la
guía desaconseja.

## Decisión

Usamos **módulo → capa**: `src/modules/<módulo>/{domain,application,infrastructure,
presentation}/`, más `src/shared/` para lo transversal a todos los módulos (config,
jerarquía de errores base, conexión a DB, middlewares, health check).

Las reglas de dependencia de §3 de la guía **no cambian**: dentro de cada módulo,
`domain` no importa frameworks, `application` solo depende de su propio `domain`,
`infrastructure` implementa las interfaces de su `domain`, `presentation` orquesta su
`application`. Se agrega una regla nueva, propia de tener varios módulos: ningún módulo
importa el `domain` o `application` de otro módulo — solo `shared`. Ambos contratos se
verifican automáticamente con `import-linter` en CI, no quedan como convención de palabra.

`ARCHITECTURE_GUIDE.md` §2 se actualiza en el mismo cambio que introduce este ADR, para que
la norma documentada y el código no diverjan.

## Consecuencias

- Positivas: una feature de un módulo vive en un solo árbol de directorios. Un módulo se
  puede leer, revisar o (en el futuro) extraer a servicio propio sin tener que recolectar
  fragmentos de 4 carpetas distintas.
- Negativas: desviación respecto al texto original de la guía — mitigado actualizando la
  guía en el mismo commit, para que no quede una excepción no documentada.
