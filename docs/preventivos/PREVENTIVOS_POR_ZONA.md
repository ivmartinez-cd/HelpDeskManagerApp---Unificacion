# Preventivos por zona — definición operativa

Módulo `preventivos` (backend `backend/src/modules/preventivos/`, frontend
`frontend/src/features/preventivos/`, pantalla `/preventivos`). Decisiones de diseño en
ADR-019; fuentes de datos confirmadas en `docs/siges/SIGES_READONLY_CATALOGO_DATOS.md` §3.

## Qué es cada cosa

- **Zona**: `Sucursal.Cuadricula` de Siges (texto libre). El catálogo que muestra la pantalla
  es el `DISTINCT` de sucursales activas con parque activo, menos la lista de exclusión
  configurable `PREVENTIVOS_ZONAS_EXCLUIDAS` (PSTs del interior y basura). Zonas locales
  actuales (2026-08-14): CABA, CABA-N, CABA-O, CABA-S, CENTRO, NORTE1-4, OESTE, SMARTIN,
  SUR, SUROESTE (+ `SUORESTE`, typo real de Gestión con 56 máquinas).
- **Frecuencia**: `Sucursal.TipoPreventivo` → `TipoPreventivo.Dias` (30/60/90/120/180/360;
  0 = sin preventivo pactado). Es un dato POR SUCURSAL: todas las máquinas de la sucursal
  comparten frecuencia. No confundir con la tabla `Frecuencia` (es de otra cosa, legacy).
- **Último preventivo**: máximo `Incidente` de tipo 102 (Preventivo) en estado terminal no
  anulado (Finalizado 500 / Cerrado 600 / Resuelto 700 / Resuelto c/pendientes 710). La fecha
  es `Fecha_Cierre`, salvo que tenga el sentinel `1900-01-01` (pasa incluso en Cerrados), en
  cuyo caso se usa `Fecha_Ingreso`.
- **Máquina activa**: `M.Estado = 0 AND M.ID_Estado_Maquina NOT IN (2, 8)` + sucursal activa
  (`S.Estado = 0`). Misma definición con paridad exacta contra el legacy (§3 del catálogo).

## Cómo se calcula el vencimiento (`domain/services/vencimiento.py`)

```
próximo vencimiento = fecha último preventivo + frecuencia (días)
vencido      si próximo < hoy           (dias_vencido = hoy - próximo)
por_vencer   si próximo <= hoy + 30 días
al_dia       si no
sin_frecuencia   si la sucursal no tiene frecuencia (Dias 0 o sin fila) — sin fecha
sin_preventivo   si nunca se registró un preventivo hecho — sin fecha
```

Regla dura: los estados `sin_*` son explícitos, nunca se inventa una fecha. "Hoy" se calcula
en hora de Argentina (las fechas de Siges son hora local).

## Habilitación (marca local, v1)

Tabla `preventivos_habilitacion`. Habilitar = marcar el equipo como "despachar técnico", con
quién/cuándo/nota. **No escribe nada en Gestión/Siges.** Se desactiva a mano (permiso
`update`) o sola cuando aparece un preventivo cerrado el día de la habilitación o después
(`deshabilitado_por = "sistema (preventivo registrado)"`). Una sola activa por máquina; el
historial se conserva.

## Endpoints

- `GET /api/preventivos/zonas` — catálogo de zonas locales (permiso `view`).
- `GET /api/preventivos/equipos?zona=SUR&estado=vencido&habilitado=true&q=...&page&size&refresh`
  — `Page` + `consultado_en` (caché TTL 5 min por zona; `refresh=true` fuerza consulta).
  Orden default: vencidos primero (más atrasado arriba), después sin preventivo, por vencer,
  al día, sin frecuencia.
- `POST /api/preventivos/equipos/{siges_maquina_id}/habilitar` (permiso `update`; body
  `{nota?}`) / `DELETE` ídem para deshabilitar.
