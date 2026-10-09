# Plan: unificar Usuarios y Empleados en "Personas"

Estado: **terminado** (2026-09-28). Las cuatro fases están hechas: Personas en `/personas`
reemplazó a Usuarios y a la pestaña Empleados, y lo viejo se retiró (fase 4).

## Problema

Hoy la misma persona puede estar cargada dos veces, en pantallas separadas y sin
sincronización:

- **Administración > Usuarios** — cuentas para entrar a la app (contraseña, permisos,
  color). Requiere permiso de administrador.
- **Gestión Humana > Gestión > Empleados** — fichas de RR.HH. (ingreso, días de vacaciones,
  sector, cargo, legajo Siges, color). Requiere `vacaciones.manage`.

Las dos se pueden vincular (un empleado apunta opcionalmente a una cuenta), pero el vínculo
se carga a mano y nombre, mail y color se editan por separado en cada lado.

### Foto actual (DB de dev, sembrada con datos reales, 2026-09-25)

| | Cantidad |
|---|---|
| Cuentas activas reales (sin placeholders) | 11 |
| Empleados (todos activos) | 42 |
| Empleados vinculados a una cuenta | 8 |
| Empleados sin cuenta (no entran a la app) | 34 |
| Cuentas activas sin ficha de empleado | 5 |
| …de esas, con un empleado del mismo mail sin vincular | 3 |
| Vinculados con mail distinto | 0 |
| Vinculados con color distinto (3 de ellos sin color en la cuenta) | 8 de 8 |

## Decisión propuesta

**Una sola lista de personas; el acceso a la app es una parte opcional de cada persona.**
No se mueve todo a Usuarios: 34 de 42 personas no entran a la app, y darle a RR.HH. la
pantalla de Usuarios obligaría a darle permiso de administrador (con acceso a los permisos
de todos).

Modelo de negocio:

- **Persona** = nombre, mail, color. Un solo lugar, vale para toda la app.
- **Datos laborales** (opcional) = ingreso, días anuales, sector, cargo, legajo Siges,
  estado. Los edita quien tiene `vacaciones.manage`.
- **Acceso a la app** (opcional) = activa/inactiva, contraseña, superadmin, permisos. Lo
  edita solo el administrador.

Cómo se ve:

- Una pantalla **Personas** (reemplaza a Administración > Usuarios y a la pestaña Empleados).
  Tabla con nombre, mail, sector, cargo, "entra a la app sí/no", estado; columnas ordenables.
- Ficha de persona con pestañas **Datos**, **Laboral**, **Acceso**. Cada usuario ve solo las
  pestañas que su permiso habilita.
- Desde Gestión Humana, el acceso a "Empleados" lleva a Personas filtrado por
  "con datos laborales"; RR.HH. no ve la pestaña Acceso.
- "Dar acceso a la app" a una persona existente crea la cuenta con su mail y la vincula en el
  mismo paso (hoy son dos altas separadas + vínculo manual).

## Enfoque técnico

Las dos tablas actuales (`app_user` y `vacaciones_empleado`) **se mantienen**: hay 33 claves
foráneas que apuntan a `app_user` (turnos, prestadores, contadores, insumos, preventivos,
permisos, sesiones y el propio vacaciones), y 5 que apuntan a `vacaciones_empleado`.
Fusionarlas en una tabla nueva es una migración grande con riesgo alto y ninguna ventaja
visible para el usuario. Lo que cambia es:

1. **Vínculo obligatorio cuando corresponde.** Si una cuenta y un empleado tienen el mismo
   mail, quedan vinculados (validación al crear/editar, no solo convención).
2. **Nombre, mail y color, una sola fuente de edición.** La ficha unificada escribe en los dos
   lados en la misma transacción. Editar desde un lado solo ya no es posible porque las
   pantallas viejas desaparecen.
3. **Lectura unificada en el backend.** Un endpoint paginado (`Page[T]`) que devuelve las
   fichas con su cuenta si la tienen (toda cuenta nace de una ficha), con filtro, búsqueda y
   orden en el servidor.
   Ubicación propuesta: módulo nuevo `personas` que solo compone (lee de ambos, delega las
   escrituras a los casos de uso existentes de auth y vacaciones). Hoy vacaciones ya depende
   de auth y no al revés; `personas` depende de los dos y nadie depende de `personas`.
   Requiere **ADR** (nuevo módulo de composición) y un contrato de import-linter nuevo.
4. **Permisos propios** (decisión 2026-09-25): `personas.view`, `personas.update` (nombre,
   mail, color) y `personas.manage` (dar/quitar acceso). Backfill desde `vacaciones.manage` /
   `admin.manage`. Cambiar el mail de quien entra a la app exige `manage`. Los datos
   laborales se siguen editando con `vacaciones.manage` por `/api/vacaciones/empleados`.
   **Alcance por sector (2026-10-09)**: quien tiene sector asignado como jefe en Gestión de
   Personal (`user_module_scope` de vacaciones) solo ve y edita personas de su sector en
   listado, ficha, datos y acceso, tenga o no `manage`; las de otro sector responden 404.
   El superadmin ve a todos (`PersonasDelSector` en `application/use_cases/alcance_sector.py`).

## Limpieza de datos (antes de la migración)

Migración de datos única (Alembic), precedida de `make db-backup TAG=personas-unificacion`:

| Caso | Acción propuesta | ¿Automática? |
|---|---|---|
| Leonardo Pressburger, Ariel Otero, Juan Pablo Corigliano: cuenta activa + empleado con el mismo mail sin vincular | Vincular | Sí |
| Empleado "Ivan Martinez" vinculado a la cuenta inactiva `imartinez@…` | Vincular a `admin@example.com` (la cuenta que usa); la ficha conserva `imartinez@…` | Sí (decidido) |
| "Marcia Pollero", vinculada al placeholder "Pollero (ex-operador)" | Es ex empleada: ficha a inactiva, se conserva el vínculo y su historial | Sí (decidido) |
| Franco Lombardi: ficha `flombardi@…`, cuenta `cds@…` | Es empleado: la ficha pasa a `cds@…` y se vincula | Sí (decidido) |
| Vinculados con color distinto | Gana el de la cuenta; si la cuenta no tiene, se le copia el de la ficha | Sí (decidido) |
| 7 fichas con espacios de más en nombre o apellido | Normalizar espacios | Sí |
| Cuenta de prueba inactiva "Smoke Vacaciones" | Dejarla, no aparece por estar inactiva | — |

## Fases

1. **Decisiones + limpieza de datos.** Responder las preguntas de abajo; migración de datos;
   validación de vínculo por mail al crear/editar en las pantallas actuales. Chico, se puede
   hacer ya y reduce el problema aunque no se siga.
2. **Backend `personas`.** ADR, endpoint de listado paginado, ficha (lectura), escritura
   coordinada de nombre/mail/color, "dar acceso" y "quitar acceso". Tests unitarios +
   `make check`.
3. **Frontend Personas.** Pantalla y ficha con pestañas según permiso; Administración >
   Usuarios y la pestaña Empleados redirigen a la pantalla nueva. La pantalla de permisos por
   usuario (`/admin/usuarios/[id]/permisos`) queda como está, enlazada desde la pestaña Acceso.
4. **Retiro de lo viejo.** Borrar las pantallas/modales duplicados y los endpoints que ya no
   use nadie. Recién acá, una vez que los compañeros probaron la pantalla nueva.

Cada fase se puede cortar y dejar andando sola.

## Fase 2: qué quedó hecho

Endpoints (`/api/personas`, ADR-040):

| Método | Ruta | Permiso | Qué hace |
|---|---|---|---|
| GET | `/api/personas` | `view` | Lista paginada; filtros `q`, `sectorId`, `activa`, `entraALaApp`; orden `sortBy` (nombre, email, sector, cargo, acceso, estado) + `sortDir` |
| GET | `/api/personas/{id}` | `view` | Ficha |
| PATCH | `/api/personas/{id}/datos` | `update` (+`manage` si cambia el mail de quien entra) | Nombre, mail y color en ficha y cuenta |
| POST | `/api/personas/{id}/acceso` | `manage` | Crea la cuenta y manda el link de activación, o reactiva la que había |
| DELETE | `/api/personas/{id}/acceso` | `manage` | Desactiva la cuenta (no la desvincula) |

Verificado contra la base de dev: 42 personas (11 entran a la app, 30 activas sin acceso, 1
inactiva); dar acceso, editar datos y quitar acceso probados en una transacción descartada.

## Fase 3: qué quedó hecho (2026-09-28)

- **Menú**: "Personas" es el primer ítem de Gestión Humana, dentro del submenú de Gestión de
  Personal (2026-09-28, pedido de Iván; al principio reemplazaba a "Usuarios" al final del
  menú). Solo aparece suelta para quien la tenga sin el módulo de Gestión de Personal. Ese
  mismo día Turnos también pasó a ese submenú (grupo "Turnos"), con el mismo criterio. El
  módulo admin ya no tiene ítem; su permiso sigue gateando la grilla de permisos. `/admin` y
  `/admin/usuarios` redirigen a `/personas`. La pestaña Empleados de Gestión de Personal ya no
  existe (`?tab=empleados` redirige) y su acceso en el submenú se sacó (2026-09-28, pedido de
  Iván: Personas se entra solo desde su ítem del menú).
- **Listado**: nombre (+mail), sector, cargo, ingreso/antigüedad y disponibles (estas dos solo
  para quien ve vacaciones: se cruzan con el listado de empleados), entra a la app, estado.
  Búsqueda y filtros por sector, acceso y estado. Trae todo en una carga (tope 200) y ordena
  y filtra en el navegador, como la vieja pestaña Empleados.
- **Ficha** `/personas/{id}` con pestañas: **Datos** (nombre, mail, color; `personas.update`;
  el mail de quien entra a la app solo con `personas.manage`), **Laboral** (ingreso, estado,
  sector, cargo, saldo y legajo Siges; se ve con `vacaciones.view`, se edita con
  `vacaciones.manage` por el ABM de empleados) y **Acceso a la app** (solo con
  `personas.manage`: dar/reactivar/quitar acceso; con `admin.manage` además Permisos y link
  de restablecimiento).
- **Alta**: "Nueva persona" crea la ficha (`vacaciones.manage`); el acceso se da después
  desde la ficha. "Vincular con Siges" se mudó a la cabecera de Personas.
- Sin "Eliminar" en la primera versión; se agregó en la fase 4 (ver abajo).
- Plantillas de permisos: Team leader suma `personas.view`/`update`; "Team leader +
  Usuarios" suma `personas.manage` (mismo criterio que el backfill).

## Fase 4: qué se retiró (2026-09-28)

- Frontend: la pantalla de Administración > Usuarios (con sus modales de alta y color) y la
  pestaña Empleados de Gestión Humana (con su modal). Los links viejos siguen redirigiendo
  a Personas.
- Backend: de `/api/admin/users` se sacaron listado, alta y edición; quedan ver una cuenta
  (grilla de permisos) y mandar el link de restablecimiento. También el orden de la lista vieja
  y la búsqueda del color en Gestión al crear cuentas: ahora el color sale de la ficha.
- **"Eliminar persona"** pasó a la pestaña Laboral (decisión de Iván): con permiso de
  gestionar vacaciones y solo si la persona no entra a la app. Pide confirmación porque borra
  en cascada sus vacaciones, ausencias y ciclos; lo normal sigue siendo pasarla a inactiva.

## Decisiones tomadas (2026-09-25)

- Marcia Pollero es ex empleada (ficha inactiva). Franco Lombardi es empleado; su mail es
  `cds@…` y su color pasó a `#f97316` para no repetir el de Ariel Otero.
- Color: gana el de la cuenta.
- **Toda persona con acceso a la app tiene ficha de empleado.** Para dar acceso primero se
  cargan los datos laborales; en la fase 2 no hay "personas solo con acceso".
- **Iván entra con `imartinez@canaldirecto.com.ar`.** Su cuenta superadmin (ex
  `admin@example.com`) tomó ese mail; la cuenta vieja quedó inactiva como
  `imartinez-cuenta-vieja@example.invalid` y sus 5 registros de historial de asignación de
  prestadores pasaron a la cuenta actual. Backup previo:
  `backups/helpdesk-db_2026-09-25_1627_pre-mail-ivan.dump`.
- Las dudas nuevas se consultan en el momento en que aparecen.
- Permisos propios de Personas con backfill (fase 2).

## Preguntas abiertas (para Iván)

- Ninguna. Nombre de la pantalla: "Personas" (2026-09-28); ingreso y saldo en el listado y
  Personas en lugar de Usuarios en el menú (2026-09-28).
