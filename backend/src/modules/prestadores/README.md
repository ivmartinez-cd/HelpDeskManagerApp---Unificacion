# prestadores

Catálogo de PST (Prestadores de Servicio Técnico) vinculado a **Siges**
(`siges_empresa_id` = `ID_Empresa` de `dbo.Empresa`), usado para asignar qué
**operador de Canal Directo** atiende a cada PST y para que el módulo `sla`
filtre incidentes por "mis PST" (`src/modules/sla/domain/repositories/prestador_lookup.py`).

**No confundir con `backend/src/modules/liquidaciones`** — ese es el motor de
preliquidaciones/validación de los 4 PST que facturan por CSV (Pentacom, Pertex-Supernova,
Infomac, Gestión Integral). Son dos catálogos de "Prestador" independientes, sin FK entre
sí, cada uno con su propio subconjunto de PST y su propio modelo de datos. Ver la nota en
`INTEGRACION_APPS_PLAN.md` (sección Fase 3 — Liquidacion-Prestadores) para el detalle
completo de la distinción.

## Modelo de datos

- `prestador` (`domain/entities/prestador.py`): `siges_empresa_id` (NOT NULL, UNIQUE),
  `den_comercial`, `razon_social`, `cuit`, `operador_id` (puntero rápido al operador
  vigente), `is_active`.
- `prestador_contacto`: nombre/teléfono/email de contacto. Un PST puede tener varios.
- `prestador_asignacion_historial`: tramos `operador_id, desde, hasta` — `hasta=None` es
  el tramo vigente. Registra la vigencia temporal de cada operador sobre un PST (ej.
  "mpollero hasta 2024-02-29, vipaez desde 2025-08-04").

## Decisión de diseño: alta manual, no auto-creación desde Siges

`SyncPrestadoresDesdeSiges` (`application/use_cases/sync_prestadores_desde_siges.py`)
**solo actualiza** `den_comercial`/`razon_social`/`cuit` de PST ya existentes — nunca crea
ni desactiva. El alta de un PST nuevo siempre es una decisión explícita desde la UI
(`CreatePrestador`), a propósito: el legacy creaba automáticamente ~29 prestadores fuera de
alcance solo por aparecer en la consulta de Siges.
