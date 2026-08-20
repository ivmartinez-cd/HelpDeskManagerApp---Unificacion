# Modo vacaciones de turnos (ADR-025) — verificación en vivo 2026-08-20

Capturas tomadas contra el frontend real de dev (`localhost:3000`, build de producción del
contenedor) con el backend real (`localhost:8012`, `DISABLE_BACKGROUND_JOBS=true`), después de
sincronizar y reiniciar ambos contenedores (`scripts/wsl/sincronizar-y-reiniciar.sh`).

| Captura | Qué muestra |
|---|---|
| `01-home-badge-grilla-vacaciones.png` | Inicio › Turnos del día con el badge **"Grilla de vacaciones hasta el 21/08"** y el timeline resolviendo una variante vigente. Para la captura se creó una variante temporal (20–21/08, motivo "PRUEBA VISUAL ADR-025") que se borró de la DB de dev al terminar; `/api/turnos/current` volvió a la titular (`varianteActiva: null`) sin ninguna otra acción. |
| `02-admin-turnos-modo-vacaciones-listado.png` | `/admin/turnos?tab=vacaciones`: pestañas Grilla titular / Modo vacaciones y el listado con la grilla real **"Vacaciones M. J. Vela" 24/08 → 28/08**, 35 franjas, 5 advertencias (INSUMOS 8:00–8:30 L–V), estado **Programada** (derivado por fecha). |
| `03-editor-precargado-caso-majo.png` | Editor abierto por el deep link del CTA de Aprobaciones (`?tab=vacaciones&ausente=<Majo>&desde=2026-08-24&hasta=2026-08-28&motivo=…`): precarga automática de la grilla titular con las franjas de Majo marcadas como hueco a cubrir. |
| `04-editor-recorte-advertencia-hueco.png` | Tras re-cortar INSUMOS 8–11 → 8:30–11 con Mariano: advertencia **"INSUMOS · Lunes sin cobertura 08:00–08:30 (la titular sí la cubre)"** + franjas sin operador; **Guardar sigue habilitado** (los huecos no bloquean). |
| `05-admin-turnos-grilla-titular.png` | Pestaña Grilla titular (sin cambios funcionales); el botón que antes decía "Modo vacaciones" y llevaba a Coberturas ahora dice **Coberturas**. |

## Estado cargado en dev

- `turno_grilla_variante` tiene la variante real del caso
  (`docs/coberturas/PLAN_COBERTURA_VACACIONES_MAJO_2026-08-24.md`): id `e35e7d21-09d8-4224-911c-7d6378779278`,
  24–28/08/2026, ACTIVA, 35 franjas (L–V × 7), creada vía `POST /api/turnos/grilla-variantes` con
  los usuarios reales (Mariano Villegas, Luna Torres, Victor Paez, Mariana Rodriguez). La
  respuesta trajo exactamente 5 advertencias HUECO (INSUMOS 8:00–8:30, un día cada una) y ninguna
  de cubriente ausente.
- La grilla titular (`turno_slot`/`turno_asignacion`) no se tocó. Hoy (jueves 20/08)
  `/api/turnos/current` resuelve la titular con Majo en 8–11 y 13–15; el lunes 24 a primera hora
  va a resolver la variante, y el lunes 31 vuelve sola a la titular.

## Lo que NO se verificó en vivo (y por qué)

- El banner "Armar grilla de cobertura →" de Aprobaciones exige **decidir** una solicitud. La
  solicitud real de Majo (24–28/08) ya está APROBADA en la DB de dev (datos reales de Gestión de
  Personal) y re-decidirla agregaría una fila de historial + auditoría sobre un registro real, así
  que no se hizo. El flujo está cubierto por `frontend/tests/modo-vacaciones.spec.ts`
  (mock de `POST /decision` con `afectaTurnos`) y por los tests unitarios de `DecidirSolicitud`
  + el test de integración de `SqlAlchemyImpactoTurnosLookup` contra Postgres.
