# ADR-045: Vitest para la lógica pura del frontend

## Estado: Aceptado (2026-10-01)

## Contexto

`ARCHITECTURE_GUIDE.md` §7 pide tests unitarios para la lógica de negocio, y §5 pide
justificar cada dependencia nueva. El frontend solo tenía la suite de Playwright
(`frontend/tests/`, ADR-022): flujos de pantalla con el backend mockeado, ~5 min por
corrida y sin node en el host (se corre con la imagen oficial). Mientras tanto hay ~50
módulos de lógica pura en `src/**/lib` y `src/**/utils` que deciden cosas de negocio y no
tenían ningún test: qué ruta puede abrir cada permiso (`route-permissions.ts`), validación
de solapes y huecos en grillas de turnos, dígito verificador de incidentes, semáforo de
espera de WATI, formatos de fechas e importes.

## Decisión

- **Vitest** como única dependencia nueva (dev, versión fijada). Usa la misma
  configuración de TypeScript y el alias `@/` que el resto del proyecto, y corre en
  milisegundos dentro del contenedor del frontend.
- **Solo lógica pura, en entorno `node`**: archivos `src/**/*.test.ts` junto al módulo que
  prueban. Nada de render de componentes: eso necesitaría jsdom y Testing Library (dos
  dependencias más) y lo cubre Playwright.
- `npm test` → `vitest run`; `make test-frontend`, incluido en `make check` y
  `make check-fast`.
- Primera tanda: permisos de rutas, grillas de turnos, dígito verificador, semáforo de
  WATI, input de hora y validación de URLs. El resto se suma al tocar cada módulo.

## Consecuencias

- Positivas: la lógica que decide permisos y validaciones del frontend queda verificada
  en cada `make check`, sin esperar la suite E2E.
- Negativas: una dependencia de desarrollo más que mantener. Los componentes siguen sin
  tests unitarios; si hiciera falta, se evalúa jsdom + Testing Library en otra ADR.
