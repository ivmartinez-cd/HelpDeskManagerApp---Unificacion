# ADR-039: Siges desde ORION en vez de MERCURIO

## Estado: Aceptado e implementado (2026-09-11)

## Contexto

Todo el backend consulta la base `Siges` en el SQL Server `MERCURIO.cdsa.com.ar` (ADR-018
centralizó la plomería, no eligió el host — la elección de MERCURIO es anterior, validada en
ADR-012). MERCURIO es el motor **productivo**: además de servir estas lecturas, ahí escribe
Canal Directo en producción. Iván identificó que existe `ORION` (accesible como
`Orion.cdsa.com.ar` o `reportes.cdsa.com.ar`, resuelven a la misma IP `192.168.176.21`), el
motor que usa el legacy para **consultas y reportes**, con la misma base `Siges` y la misma
cuenta de solo lectura `SiGesReadOnly`.

Pegarle a MERCURIO desde una app de pruebas (jobs de fondo corriendo cada pocos minutos +
consultas en vivo de 7 módulos) compite por recursos con el motor donde se escribe en
producción, sin ninguna necesidad: para lecturas existe un motor dedicado.

**Evidencia de paridad** (`backend/scripts/explore_orion_vs_mercurio.py`, misma cuenta contra
los dos hosts): `@@SERVERNAME` distinto (MERCURIO / ORION) confirma que son dos instancias
físicas distintas; mismo `COUNT(*)` de `dbo.Moneda` (4) y mismo `MAX(Fecha_Proceso)` de
`dbo.Factura_Anexo` (2026-09-11), relojes de servidor a menos de 1 s de diferencia. Muestra
puntual, no exhaustiva — sin lag visible.

## Decisión

### Cambiar el host, no la arquitectura

La plomería de ADR-018 (`OrionQueryRunner`, singleton por `lru_cache`, semáforo de
concurrencia, conexión efímera por consulta) no cambia. Cambia únicamente **qué SQL Server
apunta la config**: `MERCURIO.cdsa.com.ar` → `reportes.cdsa.com.ar`.

### Env vars: se renombran (deroga la sección homónima de ADR-018)

ADR-018 decidió no renombrar `sla_mercurio_*`/`SLA_MERCURIO_*` porque era "una integración
verificada en producción". Ese argumento ya no sostiene el nombre: mantenerlo diría
`MERCURIO` en el código mientras el `.env` apunta a otro servidor — confusión activa en vez
de historia inofensiva. Se corta limpio:

- `sla_mercurio_host/database/user/password/driver/encrypt/timeout_seconds` →
  `orion_host/database/user/password/driver/encrypt/timeout_seconds`, sin el prefijo `sla_`
  (nunca fue solo de `sla`; hoy lo usan 7 módulos). Nueva clase `OrionSettings` en
  `settings_groups_operativos.py`, separada de `SlaSettings`.
- `mercurio_max_concurrent` → `orion_max_concurrent`.
- `SLA_MERCURIO_*`/`MERCURIO_MAX_CONCURRENT` en `.env`/`.env.example` → `ORION_*`.
- Sin `AliasChoices` ni compatibilidad con los nombres viejos: el único entorno real hoy es
  esta máquina (el deploy a Render/Vercel/Neon está frenado por la red interna — ver memoria
  de sesión), así que no hay corte a coordinar entre entornos. Aceptar los dos nombres a la
  vez es exactamente el riesgo que ADR-018 ya había rechazado (confusión de diagnóstico entre
  entornos), y acá aplicaría con menos beneficio todavía.

### Nombres de código: `orion`, no `siges`

Se evaluó nombrar la capa `siges` (el nombre de la base, que no cambia si el host vuelve a
moverse) en vez de `orion` (el nombre del servidor actual). Se eligió **`orion`**: nombrar el
servidor deja explícito contra qué motor físico pega cada consulta — dato relevante para
diagnosticar carga o cortes de red — al costo de tener que renombrar de nuevo si el host
cambia otra vez. Carpetas `shared/infrastructure/orion/`, `sla/infrastructure/orion/`,
`bono_tecnicos/infrastructure/orion/`; `OrionQueryRunner`, `require_orion_runner()`,
`build_orion_connection_string()`. Esto deja una inconsistencia consciente: los otros 5
módulos que consultan la misma base (`contadores`, `liquidaciones`, `prestadores`,
`preventivos`, `vacaciones`) ya tenían su carpeta como `infrastructure/siges/` — no se
renombran, para no tocar más superficie de la necesaria en este cambio.

### Qué no cambió

Los 6 gateways de módulo (puertos, `query.py`, mapeo de filas), el candado de import-linter
`pyodbc-zeep-solo-infrastructure`, y las variantes `_or_none` de degradación por módulo — todo
eso es ortogonal al host y sigue igual.

## Consecuencias

- Las lecturas de Siges dejan de competir con las escrituras de producción en MERCURIO.
- Mensajes de error/log visibles a usuarios y en `docs/INTEGRACIONES_EXTERNAS.md` pasan de
  decir "MERCURIO" a decir "ORION" (`DEFAULT_ERROR_MESSAGE`, warnings de degradación en
  `contadores`/`prestadores`). En frontend (`sla-mes-card.tsx`, `sla-detail.tsx`) se optó por
  decir "Siges" en vez de "Orion": el nombre del servidor es detalle interno, no algo que el
  usuario final necesite ver.
- `scripts/sizes-baseline.json` actualizado a mano (dos rutas `.../mercurio/...` →
  `.../orion/...`) en el mismo commit — no se corrió `--update` completo para no arrastrar
  WIP de otras sesiones en el árbol de trabajo.
- Riesgo aceptado: la paridad Orion/Mercurio se verificó en una muestra puntual (2 tablas), no
  exhaustiva. El rollback si aparece un dato divergente es una sola variable de entorno
  (`ORION_HOST=MERCURIO.cdsa.com.ar`), sin volver a tocar código.
- `backend/scripts/` (67 archivos de exploración one-off) se actualizó en el mismo `sed` que
  el código de producción — no corren en CI, pero quedarían rotos si no se tocaban.
