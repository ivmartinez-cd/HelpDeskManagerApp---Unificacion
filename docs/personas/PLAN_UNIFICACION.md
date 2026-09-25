# Plan: unificar Usuarios y Empleados en "Personas"

Estado: **fase 1 en curso** (2026-09-25). Autovínculo por mail implementado; limpieza de
datos lista en `limpieza_fase1.sql`, pendiente de correr.

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
3. **Lectura unificada en el backend.** Un endpoint paginado (`Page[T]`) que devuelve la unión
   "empleados ∪ cuentas no vinculadas", con filtro, búsqueda y orden en el servidor.
   Ubicación propuesta: módulo nuevo `personas` que solo compone (lee de ambos, delega las
   escrituras a los casos de uso existentes de auth y vacaciones). Hoy vacaciones ya depende
   de auth y no al revés; `personas` depende de los dos y nadie depende de `personas`.
   Requiere **ADR** (nuevo módulo de composición) y un contrato de import-linter nuevo.
4. **Permisos:** listar y editar Datos/Laboral con `vacaciones.manage` o admin; Acceso solo
   admin. Sin permisos nuevos.

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

## Decisiones tomadas (2026-09-25)

- Marcia Pollero es ex empleada. Franco Lombardi es empleado y su mail es `cds@…`.
- La ficha de Iván se vincula a `admin@example.com`.
- Color: gana el de la cuenta.
- Las dudas nuevas se consultan en el momento en que aparecen.

## Preguntas abiertas (para Iván)

- **¿Toda persona con acceso debe tener ficha de empleado?** Hoy solo queda
  `admin@example.com` sin ficha propia (usa la de `imartinez@…`). Bloquea la fase 2.
- **Nombre de la pantalla**: "Personas" o "Equipo". Bloquea la fase 3.
- **Mail de Iván**: tras la limpieza su ficha dice `imartinez@…` y su cuenta
  `admin@example.com`; es el único vinculado con mails distintos. Bloquea la fase 2 (la
  ficha unificada tiene un solo mail).
