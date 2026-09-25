# ADR-040: Personas — módulo de composición sobre cuentas (auth) y fichas (vacaciones)

## Estado: Aceptado (2026-09-25)

## Contexto

La misma persona podía estar cargada dos veces: como **cuenta** en Administración > Usuarios
(`app_user`, módulo `auth`) y como **ficha de empleado** en Gestión de Personal
(`vacaciones_empleado`, módulo `vacaciones`), con un vínculo opcional cargado a mano y nombre,
mail y color editados por separado. El plan de unificación
(`docs/personas/PLAN_UNIFICACION.md`) decidió, con Iván:

- Una sola lista de **personas**. La ficha de empleado es la persona; el acceso a la app es
  opcional. **Toda cuenta nace de una ficha** (no hay personas "solo con acceso").
- No fusionar las tablas: 33 claves foráneas de 7 módulos apuntan a `app_user` y 5 a
  `vacaciones_empleado`. Fusionarlas es una migración grande sin beneficio visible.
- Permisos propios de Personas (no reusar `vacaciones.manage` / `admin.manage`, que §8 de la
  guía prohíbe "prestar").

La pantalla necesita leer y escribir en tablas de dos módulos a la vez, y la guía (§2, variante
monolito modular) dice que ningún módulo importa el `domain` o `application` de otro.

## Opciones evaluadas

**A — Poner Personas dentro de `vacaciones`.** Ya lee `app_user` en su infrastructure. Descartada:
la pantalla es de administración de gente, no de vacaciones; dar y quitar acceso a la app sería
responsabilidad de Gestión de Personal, y el permiso de gestionar accesos quedaría colgado de un
módulo que no es el suyo.

**B — Poner Personas dentro de `auth`.** Descartada: `auth` pasaría a depender de `vacaciones`,
invirtiendo la dirección actual (hoy `vacaciones` depende de `auth`, nunca al revés).

**C — Módulo nuevo `personas`, de composición (elegida).** Depende de `auth` y de `vacaciones`
solo en `infrastructure`/`presentation`; nadie depende de él.

## Decisión

- `src/modules/personas/` con sus capas. `domain` define la entidad de lectura `Persona` y los
  puertos `PersonaRepository`, `FichasGateway`, `CuentasGateway` y `AvisoActivacion`;
  `application` tiene los casos de uso (listar, obtener, actualizar datos, dar y quitar acceso)
  y no importa ni `auth` ni `vacaciones`.
- `infrastructure` implementa los puertos cruzando módulos, con el mismo criterio que los
  gateways `infrastructure/vacaciones/` de `bono_tecnicos` y `tareas_varias`:
  - la lectura unificada consulta con SQLAlchemy los modelos de ambos módulos
    (`vacaciones_empleado` + `department` + `vacaciones_cargo` + `app_user`);
  - las fichas se escriben con el repositorio y el registrador de auditoría de `vacaciones`,
    para que la edición quede en la misma auditoría que el ABM de empleados;
  - **las cuentas se escriben a través de los casos de uso de `auth`** (`CreateUser`,
    `UpdateUser`) y el mail de activación con `RequestPasswordReset`. Es la desviación que
    documenta este ADR: `personas` importa el `application` de `auth`, cosa que §2 no permite
    en general. Se acepta porque la alternativa, reimplementar en `personas` el alta con
    contraseña inutilizable, la guarda del último superadmin y el token de activación,
    duplicaría reglas de seguridad de `auth` en un segundo lugar. La importación está
    confinada a `infrastructure/auth/` y `presentation/aviso_activacion.py`.
- Import-linter lo hace cumplir: el `domain` de `personas` no importa frameworks; su
  `domain`/`application` no importa `auth` ni `vacaciones`; y `auth`, `vacaciones`, `turnos`,
  `prestadores` y `contadores` no importan `personas`.
- Permisos (`personas.view` / `update` / `manage`), sembrados por la migración `f3c9a1d7e2b8`
  con backfill: `view` + `update` para quien tenía `vacaciones.manage` o `admin.manage`;
  `manage` para quien tenía `admin.manage`. El módulo se siembra apagado hasta que exista la
  pantalla.
- Regla de seguridad: cambiar el mail de alguien que **entra a la app** cambia con qué mail
  inicia sesión (y adónde llega el "olvidé mi contraseña"). Por eso exige `personas.manage`
  además de `update`. Sin esa regla, quien solo edita datos podría apropiarse de una cuenta,
  incluida la de un superadmin.
- Las cuentas placeholder (ex operadores históricos) no cuentan como acceso de una persona.

## Consecuencias

- Positivas: una sola fuente de edición para nombre, mail y color; alta de acceso en un paso;
  permisos concedibles por separado (ver, editar, gestionar accesos); las reglas de cuentas
  siguen viviendo solo en `auth`.
- Negativas: `personas` se rompe si cambia la firma de `CreateUser`, `UpdateUser` o
  `RequestPasswordReset`. Mitigado por mypy y por los tests de `tests/unit/application/personas`
  y `tests/integration/test_personas_router.py`. Mientras convivan las pantallas viejas
  (fases 2 y 3 del plan), Usuarios y el ABM de empleados todavía pueden editar nombre y color
  por separado; se retiran en la fase 4.
