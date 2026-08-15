# Gap analysis: Web-Agentes → HelpDesk Manager

Relevado el 2026-08-15 sobre el código real de `D:\Dev\Trabajo\Web-Agentes-master\web-agentes`
(CakePHP 2.x, app PHP en producción hoy en día en Canal Directo) y cruzado contra el estado
actual del monorepo (`INTEGRACION_APPS_PLAN.md` + `docs/INTEGRACIONES_EXTERNAS.md` +
lectura directa de `backend/src/modules/` y `frontend/src/features/`).

Web-Agentes **no es ninguna de las 6 apps del plan de unificación original** — es una app
independiente que corre en paralelo y cubre un dominio distinto (servicio técnico de campo,
gestión de dispositivos, incidentes). Todo lo que figura acá son módulos o funcionalidades
**no contempladas en ninguna Fase del plan actual**.

---

## 1. Módulos enteramente ausentes

### 1.1 Servicios Técnicos / Incidentes — PRIORIDAD MÁS ALTA

Es el módulo central de Web-Agentes (`IncidentsController`, ~1 300 líneas). No existe ni como
placeholder en el monorepo nuevo.

**Qué hace:**
- Crear/consultar/actualizar incidentes de servicio para dispositivos de impresión.
- Flujo completo: búsqueda por NroSerie → selección de tipo/causa/fuente/falla →
  creación → seguimiento por instancias → cierre.
- Gestión de repuestos por incidente: agregar, eliminar, escanear código de barras.
- Registrar reemplazos de piezas.
- Consultas / preguntas entre operador y prestador (`askfordetails`).
- Cancelar/anular un incidente.
- Formulario imprimible (`print` layout, sin navegación).
- Cálculo de costos de incidentes.
- Matriz de derivación.

**Entidades del dominio:**
- `Incident` — número único con dígito verificador módulo-N (ver §3.2), estado numérico
  (<500=abierto, <900=resuelto, ≥900=cerrado), tipo, causa, fuente, falla, mano de obra.
- `Instance` — registro de actualización de estado (bitácora de progreso).
- `Replacement` — reemplazo de pieza dentro de un incidente.
- `Repuesto` (parte) — ítem con código de barras codificado (ver §3.1).
- `IncidentType`, `IncidentCause`, `IncidentSource` — catálogos.
- `DerivationMatrix` — reglas de derivación.

**Integración externa:** wsAyC (el mismo WSDL de `wsg.cdsisa.com.ar` que ya consumen
`insumos` y `liquidaciones`). Los métodos que necesita el módulo:
- Lectura: `getOperatorIncidents`, `getAgentIncidents`, `getIncidentById`,
  `getIncidentByNumber`, `getIncidentInstances`, `getIncidentDetails`, `getIncidentJobs`,
  `getIncidentReplacements`, `getMachineIncidents`, `getMachineIncidentTypes`,
  `getTechnicians`, `getIncidentCauses`, `getIncidentSources`, `getFailureReasons`,
  `getDerivationMatrix`, `getArticleReplacements`.
- Escritura: `persistNewIncident`, `persistQuestion`, `persistIncidentsParts`,
  `deleteIncidentsParts`, `persistReplacement`, `voidIncident`.

**Regla de no-retry en escritura:** igual que `insumos` — `persistNewIncident` duplica
incidentes reales si se reintenta. Sin retry en ningún `persist*` ni `void*`.

**Permisos diferenciados por tipo de usuario:**
- Tipos 2-3 (operadores canal/gerentes): ven todos los incidentes de cualquier empresa.
- Tipo 5 (prestador): solo sus propios incidentes.
- Tipo 7 (operador especial): acceso propio.

**Notificaciones:** al crear incidente se envía mail a técnicos y gerentes vía SMTP
(el mismo mailer que ya usa `auth`).

---

### 1.2 Catálogo de Dispositivos / Máquinas

`MachinesController` (~600 líneas). Relacionado con `analisis-log-hp` (que ya existe)
pero conceptualmente distinto — es el catálogo maestro de equipos en campo.

**Qué hace:**
- Listado con filtros (empresa, sucursal, sector, rubro).
- Detalle de dispositivo (NroSerie, modelo, artículo, marca, empresa/sucursal/sector, estado,
  contadores, denominación comercial).
- Equipos en backup y equipos en mantenimiento (vistas dedicadas).
- Alta de nuevo dispositivo.

**Integración externa:** wsAyC — `getTopMachines`, `getBackupMachines`, `getMachineBySerial`,
`persistNewMachine`.

**Notas de alcance:**
- `analisis-log-hp` consume `getMachineBySerial` también, desde el adapter propio de insumos
  (`ZeepWsAycGateway`). Si se crea este módulo, reutilizar el provider compartido de ADR-018
  en vez de duplicar el cliente wsAyC.
- El estado del dispositivo (operativo, en backup, en mantenimiento) es distinto del análisis
  de logs de HP — son dos perspectivas del mismo equipo físico.

---

### 1.3 Registro de Lecturas de Contador (SOAP)

`CountersController`. **Distinto del módulo `contadores` del monorepo**, que proyecta
consumo desde SDS/ERS/FTP para generar el CSV de facturación SiGes. Este módulo es el
registro manual/operativo de lecturas en campo.

**Qué hace:**
- Listar últimas lecturas de contadores.
- Ver detalle de una lectura.
- Registrar nueva lectura (NroSerie + valor entero + fecha + usuario).

**Integración externa:** wsAyC — `getTopCounters`, `getCounterById`, `persistNewCounter`.

**Notas de alcance:** evaluar si este flujo puede integrarse como sub-sección del módulo
`contadores` existente (son lecturas manuales de campo, los proyectos de consumo son
downstream de estos mismos datos) o si merece un módulo separado.

---

### 1.4 Datos Maestros de Configuración

Cuatro módulos admin que el monorepo no tiene: `AreasController`, `BranchesController`,
`SectionsController`, `FailuresController`. En Web-Agentes son accesibles solo para
usuarios admin.

**Áreas (Centros de Costos):**
- CRUD de centros de costos por empresa.
- Asociar máquinas a centros de costo.
- wsAyC: `getCentrosDeCostos`, `getCentroDeCostosById`, `getTopMachines`,
  `voidCentroDeCostos`, `persistNewCentroDeCostos`, `persistCentroDeCostos`.

**Sucursales:**
- CRUD de sucursales por empresa.
- Carga de provincias y localidades (geolocalización).
- wsAyC: `getSucursales`, `getSucursalById`, `getSectores`, `voidSucursal`,
  `persistNewSucursal`, `persistSucursal`.
- Mail de notificación al crear una sucursal nueva.

**Sectores:**
- CRUD de sectores dentro de sucursales.
- wsAyC: `getSectores`, `getSectorById`, `voidSector`, `persistNewSector`, `persistSector`,
  `getSucursalById`, `getTopMachines`.

**Motivos de Falla:**
- CRUD de catálogo de fallas por marca.
- wsAyC: `getFailureReasons`, `getFailureReasonById`, `getBrands`, `voidFailureReason`,
  `persistNewFailureReason`, `changeFailureReason`.
- Usado en el formulario de nuevo incidente — sin este catálogo poblado, no se puede
  seleccionar la falla al abrir un incidente.

---

## 2. Funcionalidades faltantes en módulos que ya existen

### 2.1 Insumos — estado completo de solicitudes

El módulo `insumos` ya consume wsAyC y tiene pedidos de suministros. Verificar paridad
contra los estados completos que maneja Web-Agentes:

| Estado Web-Agentes | ¿Implementado en monorepo? |
|----|---|
| Abierto | Por verificar |
| Asignado | Por verificar |
| En tránsito | Por verificar |
| Entregado | Por verificar |
| Cancelado (`voidSupply`) | Sí — `voidSupply` está en el gateway |

Web-Agentes también tiene `askfordetailsClient` (consultas del cliente sobre su pedido)
y `getArticleParts` (repuestos disponibles para un artículo). Verificar si el monorepo
los implementa o si quedaron fuera del scope.

### 2.2 Liquidaciones — integración wsAyC para sincronización de estado

El monorepo tiene `ZeepCdLiquidacionesGateway` con `getTopLiquidations`,
`getLiquidationDetails`, `setLiquidationStatus`, `voidLiquidation`. Web-Agentes expone
además bitácoras de cambio, períodos múltiples por liquidación, adjuntos (facturas/PDF),
y consultas/observaciones con historial.

Si en algún momento el monorepo necesita exponer liquidaciones a prestadores externos
(los mismos que acceden a Web-Agentes hoy), hay que agregar:
- `getLiquidationPeriods` — períodos por liquidación.
- `getLiquidationResume` — resumen financiero.
- `persistQuestion` — observaciones/consultas sobre una liquidación.
- `getBitacora` — historial de cambios de estado.
- Upload de adjuntos (facturas, recibos) — Web-Agentes soporta JPG/PNG/GIF/PDF hasta 2 MB.

---

## 3. Componentes técnicos reutilizables a portar

### 3.1 Codec de Códigos de Barras

Web-Agentes tiene una clase `CodigoBarrasCodec` (en `app/Lib/CodigoBarrasCodec.php`)
que codifica/decodifica números de repuesto para escaneo con pistola de código de barras
usando un checksum CRC8. Si el módulo de Incidentes llega a implementarse, este codec
hay que portarlo a Python (clase pura, sin dependencias de framework).

**Algoritmo:** CRC8 como dígito verificador, concatenado al número de repuesto, encodificado
en una representación escaneable. Relevarlo del PHP antes de implementar.

### 3.2 Dígito Verificador para Números de Incidente

Web-Agentes genera un dígito verificador tipo módulo-N para el número de incidente
(`_GeneraDigitoVerificador`, `_CodificaNumeroDeIncidente`, `_DecodificaNumeroDeIncidente`).
Produce un código legible como `"1234-5"` y permite validar que el número no se haya
ingresado con error tipográfico.

El monorepo ya usa dígito verificador módulo-10 para liquidaciones (ADR mencionado en
`INTEGRACION_APPS_PLAN.md` §1). Verificar si el algoritmo es el mismo o distinto —
si es el mismo, extraerlo a `shared/domain/` como servicio puro.

### 3.3 Filtros Persistentes por Sesión

Web-Agentes guarda los filtros aplicados en sesión PHP y los restaura en la próxima visita
al listado. El equivalente en el monorepo puede ser estado de URL (`searchParams`) o
localStorage — pero hay que decidirlo y hacerlo consistente entre módulos. Hoy algunos
módulos del monorepo no restauran el filtro anterior al volver desde el detalle, lo que
obliga al usuario a volver a filtrar desde cero.

### 3.4 Formularios Imprimibles

Web-Agentes tiene un layout `print` (sin sidebar, sin navegación) activado por
`/incidents/printform`. El equivalente moderno en Next.js es una página con
`print:hidden` en los elementos de UI y `print:block` en el contenido del documento,
o una ruta `/imprimir` con un layout limpio. No existe en ningún módulo del monorepo hoy.

---

## 4. Patrones del legacy que NO hay que replicar

### 4.1 SOAP como única fuente de verdad de datos

Web-Agentes no tiene DB local — todo va y viene por SOAP. El monorepo tiene su propio
Postgres consolidado. Al portar un módulo de Web-Agentes, la decisión arquitectónica es:
- Persistir en Postgres local y sincronizar con wsAyC (patrón actual de `insumos` y
  `liquidaciones`).
- O consumir wsAyC on-demand sin persistencia local (más simple pero más frágil ante caídas).

El patrón del monorepo (persist local + sync) es el correcto para resiliencia; documentarlo
como ADR cuando se arranque el módulo de Incidentes.

### 4.2 Autenticación vía SOAP

Web-Agentes autentica contra un `getUser()` SOAP externo. El monorepo tiene su propio
auth con JWT + Argon2 + matriz de permisos. No replicar la delegación a SOAP — los
usuarios de Web-Agentes tendrán que tener cuenta en el monorepo o la migración tendrá
que mapear sus credenciales.

### 4.3 Tipos de usuario numéricos

Web-Agentes usa `id_tipo` numérico (1=admin, 2=canal, 3=gerente, 5=prestador, 6=sin-liq,
7=operador) para controlar acceso en el controller. El monorepo tiene una matriz
usuario × módulo × acción editable desde la UI — no hardcodear roles numéricos,
modelar los permisos como acciones dentro del módulo (ver `well_known_permissions.py`
en cada módulo existente).

### 4.4 Sesiones en caché sin expiración clara

Web-Agentes guarda la sesión en caché con timeout de 240 min. El monorepo usa
`session_token` en DB con TTL y revocación explícita — no cambiar ese modelo.

### 4.5 Credenciales en cookie

Web-Agentes tiene auto-login guardando usuario/contraseña encriptados en cookie
(`CD_Template`). No portar este mecanismo — el monorepo usa tokens JWT y "recordar
dispositivo" puede implementarse con refresh token de vida larga, no con credenciales.

### 4.6 `except Exception: pass` implícito (datasource SOAP silencia errores)

El datasource PHP de Web-Agentes silencia `SoapFault` parcialmente. El monorepo ya tiene
la regla §6 de `ARCHITECTURE_GUIDE.md`: ningún `except Exception` en silencio.

---

## 5. Orden de prioridad sugerido

| # | Qué | Por qué primero |
|---|-----|-----------------|
| 1 | **Módulo de Incidentes (STC campo)** | Es el módulo central de Web-Agentes, el de mayor uso diario. Tiene dependencia de los catálogos (tipo, causa, fuente, falla) y del catálogo de dispositivos. |
| 2 | **Catálogo de Dispositivos** | Prerequisito de Incidentes (el formulario de nuevo incidente requiere buscar el equipo por NroSerie). También relacionado con `analisis-log-hp`. |
| 3 | **Datos Maestros (Sucursales, Sectores, Áreas, Motivos de Falla)** | Prerequisito de Incidentes (el formulario los usa como catálogos). Se pueden portar en paralelo con el catálogo de dispositivos. |
| 4 | **Registro de Lecturas de Contador (SOAP)** | Flujo operativo de campo independiente. Evaluar integración con el módulo `contadores` existente. |
| 5 | **Ampliación de Liquidaciones** (adjuntos, bitácora completa, consultas) | Solo si el monorepo necesita dar acceso a prestadores externos (los que hoy usan Web-Agentes). |

---

## 6. Checklist antes de arrancar el módulo de Incidentes

- [ ] Relevamiento de los métodos wsAyC que necesita (la lista de §1.1 es una primera
      pasada desde el código PHP — verificar WSDL real para firmas exactas y tipos).
- [ ] Confirmar que el `WsAycClientProvider` de `shared/infrastructure/wsayc/` y el
      gateway de `insumos` soportan los métodos nuevos o si hay que crear un gateway
      separado para el módulo de incidentes.
- [ ] Tests de caracterización: levantar Web-Agentes localmente (o leer capturas del
      sistema real), documentar el comportamiento de los flujos críticos (crear incidente,
      agregar repuesto, cambiar estado) antes de escribir código.
- [ ] Diseño del schema Postgres local para Incidentes: decidir qué se persiste local
      y qué se consulta on-demand por wsAyC. Mínimo: `incidents`, `instances`,
      `replacements`; los catálogos (tipos, causas, fuentes, fallas) probablemente
      conviene cachearlos local con TTL o poblados al inicio.
- [ ] ADR de decisión persist-local vs. on-demand para este módulo.
- [ ] Design handoff antes de tocar el frontend (seguir el mismo proceso que los
      módulos anteriores — no inventar UI desde cero).
- [ ] Portear `CodigoBarrasCodec` a Python como clase pura con tests de
      caracterización (round-trip encode/decode) antes de enchufar al endpoint.
- [ ] Definir permisos well-known: `VIEW`, `CREATE`, `UPDATE`, `MANAGE` como mínimo.
      Evaluar si `CANCEL` (anular incidente) merece permiso aparte.
