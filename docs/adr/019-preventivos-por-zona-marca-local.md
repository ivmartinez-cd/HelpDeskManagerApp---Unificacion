# ADR-019: Módulo preventivos — zonas de Siges, consulta en vivo y habilitación como marca local

## Estado: Aceptado

## Contexto

El equipo local (técnicos propios de Canal Directo, no PSTs del interior) despacha
mantenimientos preventivos por zona de distribución geográfica. Hasta ahora la única forma de
saber "qué equipos de la zona SUR se quedaron sin preventivo" era mirar equipo por equipo en
Gestión. Se necesita una pantalla que liste el parque activo de una zona con su último
preventivo, su frecuencia pactada y el vencimiento calculado, y que permita marcar equipos como
"habilitados" para despachar al técnico.

La investigación de fuentes (2026-08-14, scripts `backend/scripts/explore_siges_preventivos_*.py`,
hallazgos volcados en `docs/siges/SIGES_READONLY_CATALOGO_DATOS.md` §3) fijó las definiciones
operativas:

- **Zona** = `Sucursal.Cuadricula` (texto libre, sin catálogo ni FK; único lugar del esquema
  con ese dato — `Empresa` no tiene zona y `dbo.Distribucion` resultó ser el catálogo de
  transportistas, no de zonas). El catálogo real es el `DISTINCT` de sucursales activas.
- **Frecuencia** = `Sucursal.TipoPreventivo` → `TipoPreventivo.Dias` (por sucursal;
  0 = sin preventivo pactado). La tabla `Frecuencia` (Mensual/Bimestral/…) NO es esto.
- **Último preventivo** = `MAX` de `Incidente` tipo 102 (`Tipo_Incidente` 102 = Preventivo)
  en estado terminal no anulado (500/600/700/710); fecha efectiva `Fecha_Cierre` salvo
  sentinel `1900-01-01`, en cuyo caso `Fecha_Ingreso`.
- **Universo** = `M.Estado = 0 AND M.ID_Estado_Maquina = 1` ('Activa en Cliente') + empresa
  cliente real (`E.Estado = 0 AND E.ID_Tipo_Empresa IN (101, 102)`) + **cliente vivo por
  actividad**: alguna toma de contador o algún incidente de la empresa en los últimos
  `PREVENTIVOS_MESES_ACTIVIDAD` meses (default 3). Ajustado el mismo día en dos pasadas
  tras reportes del usuario: (1) el `NOT IN (2, 8)` del parque por PST dejaba pasar
  máquinas en Baja Solicitada/No Localizado/Backup/Desguace y el tipo de empresa sin
  filtrar mostraba a CD1 (tipo 201) como cliente; (2) las bajas de facto tipo Garbarino
  tienen TODO activo en Gestión (empresa, máquinas y anexo) y solo la falta de actividad
  las delata — ni el estado ni la fecha del anexo discriminan (54% del universo vivo tiene
  anexo vencido en tácita reconducción). Ver el detalle en el catálogo de datos §3.

## Decisiones

### 1. Módulo nuevo `preventivos` (no colgar de `parque_impresoras` ni `stc`)

`parque_impresoras` y `stc` están reservados para las migraciones de Printer-Logs-Analyzer y
STC Cloud; esto es una feature nueva, no una migración. Módulo `preventivos`, ruta
`/preventivos`, ícono `calendar-clock` (`wrench` ya es de prestadores), acciones `view`/`update`,
seed en dos migraciones (deshabilitado primero, activación al final — patrón sla/contadores).

### 2. Consulta en vivo, sin snapshot local ni job de fondo

Medido con 3 corridas por zona (ronda 3): 0.18-0.42 s para 1400-1900 filas. Muy por debajo del
umbral de 5 s que hubiera justificado el patrón snapshot+job de sla. El gateway usa el
`MercurioQueryRunner` compartido (ADR-018) con el timeout general (30 s) y una caché TTL de
5 minutos por zona (la UI pagina/filtra sobre el mismo universo; `consultado_en` alimenta el
sello "datos de las HH:mm" y el botón Actualizar fuerza refresh). Sin job de fondo → sin
interacción con `DISABLE_BACKGROUND_JOBS`.

### 3. "Habilitar" en v1 es una marca LOCAL, sin escribir en Gestión/Siges

Tabla propia `preventivos_habilitacion` con auditoría (quién habilitó —
`habilitado_por_user_id` FK a `app_user` + snapshot del nombre —, cuándo, nota opcional).
La lista de habilitados es la herramienta del operador para despachar; **nada de lo que hace el
usuario acá modifica Gestión**. Crear el incidente preventivo real vía wsAyC
(`persistNewIncident`) queda explícitamente FUERA de este alcance — si se decide, es otro plan
con su propio dryRun (escritura real contra producción). `habilitado_por` sale siempre de la
identidad de sesión, nunca del body.

El use case de habilitar no valida la máquina contra Siges a propósito (los ids salen del
listado de la misma pantalla; validar costaría una pasada extra por MERCURIO en cada toggle).

### 4. Ciclo de vida: vigente hasta deshabilitar a mano o hasta preventivo posterior

Una habilitación activa se desactiva sola cuando el equipo registra un preventivo cerrado con
fecha igual o posterior al día de la habilitación (el pedido ya se cumplió). La limpieza corre
en el listado (único punto que ya cruza Siges + habilitaciones) y deja auditoría:
`deshabilitado_por = "sistema (preventivo registrado)"`. La desactivación manual guarda el
nombre del usuario. Sin vencimiento por días (descartado por el usuario). A lo sumo una
habilitación activa por máquina (índice único parcial); las desactivadas quedan como historial.

### 5. Visibilidad: todas las zonas locales para todo usuario con `view`

Sin filtro por operador — distinto criterio que sla/stc (que filtran por prestador asignado):
las zonas son geografía local, no cartera de PST. Confirmado por el usuario: la pantalla es
para el despacho de técnicos locales.

### 6. Zonas locales por lista de exclusión configurable (no hay regla de datos)

No existe en Siges una marca "zona local vs interior": las cuadrículas de PST (INTERIOR,
BSAS.*, CBA..*, …) y las locales usan la misma columna, y el prestador no discrimina (632
sucursales de INTERIOR también tienen prestador CD — ronda 4). Se excluye por patrones
configurables (`PREVENTIVOS_ZONAS_EXCLUIDAS`, default en settings: INTERIOR, A DEFINIR,
PROPIO, KIKO, 0000000000, BSAS.*, CBA..*, CUYO.*, NOA..*, COSTA*). Es lista de **exclusión** a
propósito: una zona local nueva (NORTE5) aparece sola sin tocar código ni config. Los valores
sucios que son zonas locales reales (`SUORESTE` typo, 56 máquinas) se muestran tal cual — son
datos de Gestión que conviene ver y corregir allá, no maquillar acá.

## Consecuencias

- Regla de negocio dura: un equipo sin frecuencia (`Dias = 0`/sin fila) o sin preventivo
  previo se muestra con estado explícito (`sin_frecuencia` / `sin_preventivo`), nunca con una
  fecha inventada. El cálculo es dominio puro (`domain/services/vencimiento.py`) con tests.
  **Ajuste 2026-09-02 (pedido del usuario)**: los equipos sin frecuencia directamente no se
  listan — el filtro `ISNULL(TP.Dias, 0) > 0` vive en las tres consultas de Siges para que
  tabla, chip de zona y mapa coincidan; `sin_frecuencia` queda como red de seguridad del
  dominio, no como estado visible.
- La card de Inicio queda como extensión posible (Inicio ya tiene 4+ cards) — no en esta
  pasada.
- Si el parque crece un orden de magnitud y la consulta pasa de ~0.5 s a >5 s, la decisión 2
  se revisa contra el patrón snapshot de sla (`RefreshPreventivosSnapshot` quedó descrito en el
  master prompt, no implementado).
