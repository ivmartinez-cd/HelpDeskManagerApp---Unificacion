# ADR-036: Avisos de WATI solo al operador que cubre ST, como modal de acuse obligatorio

## Estado: Aceptado (2026-09-07)

## Contexto

Desde el 2026-08-20 el frontend avisa cuando un chat de WhatsApp (WATI) cruza un umbral de
espera sin respuesta humana (15 min "atención", 60 min "crítico"): toast persistente de
`sonner` + sonido, disparados desde `WatiPendientesProvider` para **todo** usuario con el
módulo `wati` habilitado, en cualquier pantalla. El pedido del 2026-09-07 fue: "las
notificaciones de WATI deberían aparecer solo para el operador que esté en el horario de ST,
preferentemente ventana emergente que no lo deje seguir si no lo ve". El toast en la esquina
se pasaba por alto y, además, le llegaba a gente que no tenía que actuar (TL, otros
operadores fuera de turno).

Ya existía en `WatiHeaderLink` la lectura de `/api/turnos/current` para destacar el ícono
durante el horario de la casilla "ST", pero solo miraba la franja, no quién la cubría.

## Decisión

1. **Quién recibe el aviso**: solo el usuario logueado que figura como operador de una franja
   de la casilla `ST` vigente en este momento (`esOperadorStEnTurno` en
   `features/wati/utils/turno-st.ts`). Los turnos vienen resueltos por el backend con
   vacaciones e intercambios (ADR-025/026), así que "quien figura" es quien de verdad cubre.
   Fuera del horario de ST, o si el usuario no es quien lo cubre, **no se avisa a nadie**: el
   badge del header, la card de Inicio y `/wati` siguen mostrando la cola a todos (son
   informativos, no avisos).
2. **Cómo se avisa, en dos escalones** (ajuste del mismo día: "el modal solo a la hora,
   antes seguir con el toast"): a los 15 min ("atención") el toast persistente de `sonner`
   que ya existía, que se da por avisado al mostrarse y se retira solo cuando el chat pasa
   a crítico o deja de esperar; a la hora ("crítico") `BrandModal` con `dismissible={false}`
   (sin X, sin Escape; prop nueva), que lista los chats y solo se cierra con "Abrir WATI"
   (abre la inbox en otra pestaña) o "Ya lo vi". Ambos botones confirman todos los chats
   listados. Sonido de dos tonos por cada chat nuevo en cualquiera de los dos escalones.
3. **De-dup y persistencia**: clave `wa_id:nivel`; un chat avisa una vez por escalón (toast
   en "atención", modal en "crítico"), y si deja de estar pendiente su confirmación se olvida (si vuelve
   a esperar, avisa de nuevo). Las confirmaciones viven en `sessionStorage`
   (`avisos-store.ts`, store externo leído con `useSyncExternalStore` para no hacer
   `setState` dentro de efectos), así una recarga no re-abre lo ya confirmado, pero un chat
   sin confirmar reaparece.
4. **Un solo lector de turnos por pestaña**: `useTurnoSt` en el provider (fetch cada 5 min,
   reevaluado cada minuto con la hora local para no depender del `isCurrent` del fetch);
   `WatiHeaderLink` consume `enHorarioSt` del contexto en vez de pedir los turnos por su cuenta.
   El provider recibe `watiUrl` del layout para activar la lectura también cuando el usuario
   no tiene el módulo pero sí hay URL (comportamiento previo del ícono).

## Consecuencias

- Positivas: el aviso llega a una sola persona, la responsable en ese momento, y no se puede
  ignorar sin un clic explícito. Menos ruido para el resto. Un poller de turnos menos.
- Negativas: si no hay nadie asignado a ST en ese horario (grilla incompleta, feriado sin
  turno) no se avisa a nadie; la cola sigue visible en el badge/card pero sin empuje. Si la
  casilla se renombra (hoy `"ST"`, comparación sin distinguir mayúsculas), hay que actualizar
  `CASILLA_ST`.
- El modal es global (vive en el layout de `(app)`): puede aparecer encima de cualquier
  pantalla, incluso a mitad de un formulario. Es lo pedido ("que no lo deje seguir"); el
  contenido del formulario no se pierde porque el modal no navega.
