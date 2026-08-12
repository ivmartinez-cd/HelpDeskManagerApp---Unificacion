# ADR-010: Despacho de mail de los jobs de fondo con sesión propia (`LoggedMailDispatcher`)

**Estado**: Aceptado
**Fecha**: 2026-08-12
**Afecta**: `backend/src/modules/insumos/`

---

## Contexto

Dos jobs de fondo del módulo insumos mandan mail sin dejar rastro en `mail_log`: el aviso
diario de pedidos por vencer (`background_pending_alert_task`) y la alerta de poller de
insumos caído/recuperado (`PollerAlerts`). Además, `PollerAlerts` se construye una sola vez
en el lifespan de la app (`shared/presentation/app.py`) con los destinatarios de logística
resueltos en ese momento — cambiarlos en Configuración no tiene efecto hasta reiniciar el
proceso, un bug latente.

Los dos puntos de envío tienen formas distintas:

- `_run_pending_alert_cycle` ya tiene una `AsyncSession` abierta y otro trabajo transaccional
  (`mark_notified`) en el mismo ciclo — puede escribir `mail_log` directo, en la misma
  transacción.
- `PollerAlerts` vive en `application/jobs/` y no tiene sesión ni sessionmaker — construirla
  ahí violaría la separación de capas (`application` no abre sesiones de BD).

## Decisión

Partir el trabajo en dos piezas:

1. **`send_mail_to_all`** (`application/jobs/mail_delivery.py`) — función pura, sin BD: hace
   el loop por destinatario sobre el `Mailer` existente (que manda de a uno) y devuelve un
   `MailDelivery` con la fila de `mail_log` ya armada (`MailLogRecord`) y cuántos destinatarios
   la recibieron.
2. **`MailDispatcher`** (`domain/repositories/mail_dispatcher.py`) — puerto con un solo método,
   `dispatch(message) -> None`. Su implementación real, `LoggedMailDispatcher`, **vive en
   `presentation/` y no en `infrastructure/`**: abre su propia `AsyncSession` desde
   `get_sessionmaker()`, algo que ningún otro adapter de `infrastructure/` hace — los
   repositorios de infraestructura reciben la sesión del caller, nunca la crean. Ponerla en
   `presentation` deja esa asimetría explícita en vez de esconderla detrás de la carpeta que
   normalmente aloja adapters "puros".

`PollerAlerts` pasa a conocer solo `MailDispatcher` (no `Mailer` ni destinatarios). El call
site que ya tiene sesión (`_run_pending_alert_cycle` /
`background_jobs.py::_send_pending_alert`) usa directamente `send_mail_to_all` y escribe
`mail_log` + `mark_notified` en la misma transacción — no pasa por `MailDispatcher`, porque
ya tiene todo lo que ese puerto resolvería por su cuenta.

`LoggedMailDispatcher.dispatch` **nunca propaga excepciones**: las atrapa y loguea con
`exc_info`. Es un contrato explícito, no un accidente — `record_failure`/`record_success` de
`PollerAlerts` se invocan desde `_run_sync_cycle` sin una red de contención propia para el
envío de mail; si `dispatch` propagara, un fallo de SMTP o de la BD tumbaría la task del
poller entero.

## Opciones descartadas

### Mover `LoggedMailDispatcher` a `infrastructure/`

Es donde "debería" vivir un adapter de un puerto de dominio, pero todo adapter existente en
`infrastructure/insumos` recibe su `AsyncSession` por constructor — abrir una propia rompería
esa convención sin dejar rastro de por qué. Se prefirió violar la ubicación por capa de forma
visible (este ADR) antes que la convención de sesión por infraestructura de forma invisible.

### Refactorizar el `Mailer` de auth a multi-destinatario

El `Mailer` (`send(to, subject, body)`, un destinatario por llamada) se deja intacto — es
compartido con `auth` (aunque duplicado como Protocol por ADR-007) y cambiar su forma afecta
un componente ya estable fuera del alcance de este cambio. En vez de eso, `mail_log` modela
**una fila por envío lógico**: `recipients` es el CSV completo de a quién se le mandó, y
`success` es `True` solo si absolutamente todos los envíos individuales salieron bien — mismo
contrato de lectura que ya tenía la tabla en el legacy.

## Consecuencias

- Los destinatarios de logística se releen de `app_settings` en cada envío
  (`LoggedMailDispatcher._dispatch` hace su propio `get_all()`), en vez de quedar congelados
  al arranque del proceso — arregla el bug latente de que cambiar la config no afectaba las
  alertas del poller hasta el próximo reinicio.
- El aviso de pedidos por vencer deja de marcar `mark_notified` cuando el envío falló para
  todos los destinatarios (antes se marcaba igual, perdiendo el aviso para siempre). Si
  falló, la fila de `mail_log` con `success=False` sí se comitea — queda visible en el
  historial — pero el pedido se reintenta en el próximo ciclo diario.
- Toda la lógica de "qué contar como éxito/fallo de un envío a N destinatarios" es testeable
  sin BD ni mocks de sesión (`send_mail_to_all`), separada de "cómo se resuelven destinatarios
  y se persiste" (`LoggedMailDispatcher`, solo cubierto en integración/manual).
