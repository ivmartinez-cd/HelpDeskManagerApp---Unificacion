# Decisiones pendientes (auditoría de seguridad y arquitectura, 2026-10-01)

Cosas que quedaron abiertas en la auditoría y que **no se pueden resolver con código sin
una decisión de Iván**: cambian quién puede hacer qué, tocan datos de clientes o la forma
en que arranca la app. Al decidir una, anotar la fecha y la decisión acá y moverla a
"Resueltas".

## Pendientes

### 1. Clientes FTP marcados "Revisar" (contadores)

Desde 2026-09-30 usuario y contraseña FTP se leen de Siges (`dbo.GrupoEconomico`) y no se
editan en la app (commit `b84fbc33`). 228 clientes se vincularon solos; estos 6 siguen con
credenciales locales porque no coinciden con Siges:

| Cliente | Problema |
|---|---|
| GATE GOURMET | La contraseña de HDM difiere de la de Siges (Gategourmet) |
| MARBY | La contraseña de HDM difiere de la de Siges (Marby S.A.) |
| RED LINK | La contraseña de HDM difiere de la de Siges (Red Link) |
| Sancor | Su usuario figura en 2 grupos: Aproagro - Sancor y Prestadores de Servicio Técnico |
| GENNEIA | Usa otro servidor (`aws.cdsisa.com.ar`, no `www.cdsisa.com.ar`) |
| Roemmers - Maprimed | Su usuario (`roemmers`) no está en Siges |

Qué decidir: para cada uno, cuál dato es el correcto (corregir en Siges o descartar el
local). Para resolverlo: abrir el cliente en Contadores → Gestionar clientes, elegir su
grupo económico y guardar (pasa a leer de Siges y borra la contraseña local).
`backend/scripts/vincular_ftp_clients_orion.py` lista el estado actual sin escribir nada.

### 2. Permiso para configurar clientes FTP / ERS / SDS (contadores)

Hoy crear, editar y borrar esa configuración pide `contadores.export`. Lo coherente sería
`contadores.manage`. Si se cambia, **4 usuarios** que hoy exportan dejan de poder editar la
configuración, salvo que se les conceda `manage`.

Opciones: (a) mover a `manage` y conceder `manage` a quien corresponda; (b) dejarlo en
`export` y documentarlo como decisión.

### 3. Permiso para cancelar / descartar / ignorar (insumos)

Hoy alcanza con `insumos.create`. Pasarlo a `update` o `delete` le quita la acción a
**5 usuarios**.

Opciones: (a) mover a `update`/`delete` y conceder a quien corresponda; (b) dejarlo y
documentarlo.

### 4. Bloqueo de login por IP

El límite de 5 intentos fallidos es por mail (desde 2026-10-01 también resiste intentos en
paralelo, commit `5960dc78`). Queda que cualquiera puede trabar la cuenta de otro por 15
minutos. Para bloquear por IP, el backend tiene que recibir la IP real de cada usuario: hoy
registra siempre la del contenedor del frontend (172.x). Requiere configurar
`FORWARDED_ALLOW_IPS` con la IP del contenedor del frontend y verificar que Next reenvíe
`X-Forwarded-For`.

Qué decidir: si vale la pena (la app es interna).

### 5. Backend como root dentro del contenedor

`backend/Dockerfile` no define `USER`. Cambiarlo puede romper la escritura en las carpetas
montadas (`./backend`, `var/`). Recomendación: dejarlo hasta que haya despliegue de
producción.

### 6. Content-Security-Policy

No hay CSP (aceptado en ADR-035). Con `next dev` es difícil configurarla sin romper Fast
Refresh. Recomendación: hacerlo junto con el despliegue de producción.

### 7. "Refrescar caché" de HP (análisis de logs)

`POST /api/analisis-log-hp/devices/{id}/refresh-cache` lo puede usar cualquiera con
`view` (8 usuarios). Solo le pide a HP que refresque datos de un equipo. Recomendación:
dejarlo así.

## Resueltas

- **2026-10-01** — Aprobar vacaciones sin sector asignado aprueba para todos los sectores:
  **es a propósito** (RR.HH.). Documentado en `vacaciones/domain/services/scoping.py`.
- **2026-10-01** — Jefe de sector carga ausencias solo a su sector: **sí** (commit `a91c4733`).
- **2026-10-01** — Bloquear autoaprobación en vacaciones y Tareas Varias: **sí, ambas**
  (commits `a91c4733`, `15b51901`).
- **2026-09-30** — Credenciales FTP desde Siges al procesar: **sí**; los casos que no
  coinciden se revisan a mano antes de cambiarlos (ver pendiente 1).
- **2026-10-01** — Tamaño de funciones medido por cuerpo con margen hasta 25: **sí** (ADR-042).
