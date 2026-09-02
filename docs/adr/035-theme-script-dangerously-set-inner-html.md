# ADR-035: `dangerouslySetInnerHTML` del script de tema inicial

## Estado: Aceptado (2026-09-02)

## Contexto

`check_guards.py` detecta como `xss` (§8) cualquier `dangerouslySetInnerHTML` en
`frontend/src`. `frontend/src/shared/components/theme-provider.tsx::ThemeScript`
(agregado en el commit `4f8335b`, reemplazo de `next-themes` para Next 16) usa uno
para inyectar un script inline que aplica la clase `light`/`dark` al
`<html>` antes del primer paint — el patrón estándar de Next.js para evitar el
flash de tema incorrecto al hidratar (ver
`node_modules/next/dist/docs/01-app/02-guides/preventing-flash-before-hydration.md`).

El contenido es la constante `SET_THEME_CLASS_SCRIPT`: una plantilla fija que solo
interpola `STORAGE_KEY` (`"theme"`, literal del propio archivo, no dato externo) y
lee `localStorage.getItem(...)` en tiempo de ejecución del browser. No hay dato de
usuario, de la URL ni de una respuesta de API en el string — el guard lo marca por
la forma (`dangerouslySetInnerHTML`), no porque exista una inyección real.

## Decisión

Queda **exceptuado** en `scripts/guards-baseline.json`:

- `frontend/src/shared/components/theme-provider.tsx:33` (`xss`)

por diseño, no por descuido: es el único mecanismo soportado por Next.js para
correr JS antes de la hidratación, el contenido es una constante del módulo sin
interpolación de datos externos, y removerlo reintroduce el flash de tema que la
migración de `next-themes` vino a evitar.

## Consecuencias

- Cualquier cambio futuro que empiece a interpolar datos externos (props, query
  params, respuesta de API) en `SET_THEME_CLASS_SCRIPT` rompe esta excepción y
  necesita revisión — el string debe seguir siendo una constante del módulo.
- Nuevos usos de `dangerouslySetInnerHTML` en otros archivos siguen cayendo bajo
  el gate normal; esta ADR cubre únicamente esta entrada puntual del baseline.
