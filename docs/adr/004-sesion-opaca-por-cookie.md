# ADR-004: Sesión por cookie httpOnly con ID opaco (no JWT)

## Estado: Aceptado

## Contexto

VacaSync (la app de referencia para la UI de login) usa JWT de acceso/refresh guardados en
`localStorage`, con rol y `managedDepartmentId` embebidos como claims. Eso tiene dos
problemas que no queremos heredar: (1) `localStorage` es legible por cualquier script que
corra en la página — un XSS se lleva la sesión completa; (2) al embeber permisos en el
token, revocar o cambiar el acceso de un usuario no tiene efecto hasta que el token expira
(hasta 15 minutos), y un caso conocido de VacaSync (`dashboard.summary`) directamente
ignoraba el filtro de sector cuando el claim venía vacío, fallando *abierto*.

Este proyecto lee los permisos desde la matriz `permission_grant` en cada request en vez de
confiar en el token — así que la ventaja clásica del JWT (no consultar la DB para validar)
no aplica: la DB se consulta igual. Sin esa ventaja, mantener JWT solo suma superficie
(dos secretos que rotar, claims que sincronizar) sin beneficio real.

## Decisión

La cookie de sesión (`hdm_session`) lleva únicamente un identificador aleatorio de 32
bytes. Todo el estado de la sesión (usuario, expiración, revocación) vive en la tabla
`user_session`, indexada por el hash del identificador. La cookie es `httpOnly` (no legible
por JavaScript) y `SameSite=Lax`. Un token separado y legible (`hdm_csrf`) implementa
protección CSRF por double-submit en todo método mutante.

## Consecuencias

- Positivas: revocar una sesión es un `UPDATE` — efecto inmediato, sin esperar expiración.
  Sin secretos JWT que rotar. Inmune a robo de sesión por XSS (la cookie no es legible por
  JS). Cambiar un permiso en la matriz surte efecto en el siguiente request del usuario.
- Negativas: cada request autenticado hace una consulta a `user_session` (mitigado: es una
  consulta por índice sobre PK, y de todos modos hace falta una consulta a
  `permission_grant` en el mismo request).
