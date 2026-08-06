# ADR-006: snake_case en paquetes Python (excepción justificada a la convención kebab-case)

## Estado: Aceptado

## Contexto

`ARCHITECTURE_GUIDE.md` §4 establece kebab-case para carpetas (`user-management/`,
`order-processing/`). Python no puede importar un paquete cuyo nombre de directorio
contenga un guion (`import modules.parque-impresoras` es un `SyntaxError`) — el intérprete
exige que un nombre de paquete sea un identificador válido.

## Decisión

Los directorios que son paquetes Python importables (todo bajo `backend/src/`) usan
`snake_case` (`parque_impresoras`, no `parque-impresoras`). La convención kebab-case de la
guía se mantiene sin excepción en: el frontend (carpetas de `features/`, rutas de Next.js),
y las `key` de texto del catálogo de módulos en la base de datos (`module.key =
'parque-impresoras'`), que no son identificadores de ningún lenguaje y sí son visibles en
URLs.

## Consecuencias

- Positivas: el código Python es importable sin trucos (`importlib` con nombres
  alternativos, symlinks, etc.).
- Negativas: el nombre de un módulo de negocio se escribe distinto según el contexto
  (`parque_impresoras` en Python, `parque-impresoras` en la URL y en la DB) — mitigado
  documentándolo acá para que no se lea como inconsistencia accidental.
