# ADR-005: Catálogo de módulos/acciones en tablas, no enums ni strings libres

## Estado: Aceptado

## Contexto

La matriz de permisos necesita representar "módulo" y "acción". Tres opciones evaluadas:

1. **Enum de Postgres** — agregar un módulo nuevo exige `ALTER TYPE` (DDL en cada deploy) y
   un enum no puede llevar la metadata que el sidebar necesita para renderizarse (label,
   ruta, icono, orden, si está habilitado).
2. **Strings libres** validados solo en código — sin integridad referencial en la DB: un
   typo en `require_permission("vacaiones", "view")` crea silenciosamente un permiso que
   nunca se puede conceder, o un grant que apunta a un módulo que no existe. Inaceptable en
   una tabla de seguridad.
3. **Tablas de catálogo** (`module`, `action`, `module_action`) con clave natural de texto.

## Decisión

Catálogo en tablas, con la `key` de texto como PK (no un ID sustituto numérico). La query
más caliente del sistema — "qué puede hacer el usuario logueado" — se sirve directamente
desde `permission_grant` sin ningún `JOIN`, y las filas se leen solas en `psql` durante un
incidente. La integridad se garantiza con una foreign key compuesta de `permission_grant`
hacia `module_action`: conceder un par módulo/acción que no fue declarado en el catálogo
falla con una violación de FK, no en silencio.

El catálogo se siembra por migración (es contrato con el código); los grants son datos que
el admin edita en runtime desde la UI — esa distinción es la que permite dar acceso a un
módulo sin tocar código ni redeployar.

## Consecuencias

- Positivas: anti-typo real (constraint de DB, no solo convención), metadata del sidebar
  vive junto al permiso, agregar una acción nueva es una fila de INSERT, no una migración
  de tipo.
- Negativas: dos tablas más que en la alternativa de enum (mitigado: son de solo lectura
  desde la aplicación, cambian solo por migración).
