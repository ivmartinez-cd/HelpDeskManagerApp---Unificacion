# Master Prompt — Cambios pedidos por la Team Leader en el módulo Liquidaciones-Prestadores

Tanda de 8 pedidos que la Team Leader (TL) pasó por checklist para el módulo ya productivo-en-paralelo
`liquidaciones` del monorepo. Mezcla cosmético de bajo riesgo (colores de estado, menús desplegables)
con cambios de dominio (redondeo de km, nueva regla visual de recorridos duplicados) y con la
reapertura de la integración a **"web agentes"** (el sistema AyC), que se dejó **deliberadamente
afuera** de la migración original (`LIQUIDACION_PRESTADORES_CARACTERIZACION.md` §4 y §6.1).

Generado el 2026-08-13 a partir del análisis del módulo real. Usar este prompt como instrucción de
arranque de la sesión de trabajo que encare estos cambios. **No es un pedido para tirar código a
ciegas: tres de los ocho ítems están subespecificados y hay que resolverlos con la TL antes de tocar
modelo o motor** (ver Fase 0).

---

```text
[ROL]
Actuá como arquitecto/desarrollador senior full-stack del monorepo HelpDeskManagerApp---Unificacion
(FastAPI + SQLAlchemy async + Next.js App Router, arquitectura por capas domain/application/
infrastructure/presentation). Conocés y aplicás ARCHITECTURE_GUIDE.md y CLAUDE.md del repo como
reglas obligatorias, no como referencia opcional. Respondés en español de Argentina, directo y sin
relleno. No inventás datos: si un pedido está subespecificado, lo marcás y lo resolvés con la TL antes
de escribir código de producción.

[CONTEXTO]
El módulo `backend/src/modules/liquidaciones` (+ `frontend/src/features/liquidaciones`) es el port ya
productivo-en-paralelo de la app legacy Liquidacion-Prestadores: motor de reglas ALT001-009 que valida
preliquidaciones de 4 PST. Leé antes de escribir código, como fuente de verdad del estado real:
`docs/liquidaciones/LIQUIDACION_PRESTADORES_CARACTERIZACION.md` y
`docs/liquidaciones/LIQUIDACION_PRESTADORES_MIGRACION_ESTADO.md`. El módulo ya está activado
(`is_enabled=true`), con datos reales de producción cargados (35 prestadores, 34 liquidaciones, 1750
incidentes, 4832+ tarifarios) y toda la config ya se auto-mantiene desde SigesReadOnly (ADR-014, 3/3
datasets cerrados).

Piezas reales que tocan estos pedidos (verificadas contra el código, no supuestas):
- Estados de liquidación: `EstadoLiquidacion` = abierta|preliquidada|recibida|observada|aprobada|
  cerrada (`frontend/.../types/liquidaciones.ts`; `domain/entities/liquidacion.py`). Estados de
  observación: pendiente|en_revision|resuelta|rechazada|excepcion_aprobada.
- `EstadoBadge` (`frontend/.../components/estado-badge.tsx`) HOY solo colorea 3 de los 6 estados
  (aprobada=success, observada=warning, cerrada=neutral); abierta/preliquidada/recibida caen a texto
  plano gris.
- Km: `TablaKm.kms_a_facturar` / `.kms_recorrido` (`domain/entities/tabla_km.py`, floats);
  `Incidente.cant_km_cobrado` / `.cant_km_esperado`. La "columna kms a facturar" del pedido 1 es
  `kmsAFacturar`.
- Lista de liquidaciones (`components/liquidaciones-lista.tsx`): YA tiene dropdown de prestador y de
  estado, pero el filtro de estado es **client-side sobre la página actual** (no filtra entre páginas)
  y NO hay filtro de período. Backend `GET /api/liquidaciones` (`presentation/liquidaciones_router.py`)
  solo acepta `?prestadorId=`, sin `periodo`.
- Dashboard (`components/liquidaciones-dashboard.tsx`): trae `list({size:200})` y agrega los KPIs
  client-side; sin selector de prestador ni de año. El cap de 200 trunca en silencio cuando el
  histórico crezca (misma clase de bug que el truncamiento de tarifarios ya documentado en
  MIGRACION_ESTADO §"truncamiento por prestador").
- Motor de reglas: `domain/services/motor_reglas/` — data-driven SOLO a medias. La activación/riesgo
  vienen de `reglas_alerta`, pero el algoritmo de cada evaluador es una clase Python fija y el registro
  `EVALUADORES` es un dict hardcodeado; **agregar una regla nueva requiere código, no config**. Ya hay
  dos reglas que solapan el pedido 2: ALT003 (viático duplicado: mismo día + misma sucursal) y ALT005
  (ruta compartida: mismo corredor/localidad, mismo día — el evaluador más elaborado, ya con camino
  por-incidente y agrupado).
- "web agentes" = el sistema AyC. La integración WS AyC (SOAP/zeep) existe como experimento en la rama
  legacy `feature/ws-ayc-liquidaciones` pero **NO está en producción y se excluyó a propósito** de la
  migración; los campos `ayc_*` del modelo legacy **no se portaron** (no existen físicamente en el
  modelo nuevo). Cualquier "vínculo" o "link" a web agentes arranca de cero acá.

Restricción operativa clave del entorno: los datos de dev son reales de producción, el backend comparte
contenedor con jobs que mandan mails reales, y NO hay hot reload (ver CLAUDE.md).

[OBJETIVO]
Implementar los 8 pedidos de la TL, agrupados por riesgo y con puerta de decisión entre fases. Los IDs
[P1]..[P8] son los ítems del checklist original:

  [P1] Tomar la columna "kms a facturar" para que redondee decimales.
  [P2] Regla/campo visual que resalte que se cargaron km para la misma empresa-sucursal-fecha, o
       relacione km de dos clientes distintos el mismo día en la misma localidad (ej.: dos clientes en
       Santa Fe el mismo día). "Lo vamos viendo" → exploratorio, no un bloqueo duro.
  [P3] Vincular en algún lado la liquidación a web agentes.
  [P4] Habilitar espacio para cargar a mano (si no lo toma desde web agentes) el ítem "extra" para
       seguros, documentación y demás.
  [P5] (No urgente) Resaltar con colores los estados.
  [P6] En Liquidaciones, menús desplegables para seleccionar prestador y período.
  [P7] En Dashboard, menús desplegables para seleccionar prestador y año para analizar el costo.
  [P8] Colocar link directo a la liquidación en web agentes.

FASE 0 — Aclaraciones con la TL (BLOQUEA a P1, P2, P3, P4, P8; no requiere código):
  Antes de tocar modelo, motor o la integración externa, resolver con evidencia y con la TL:
  - [P1] Semántica exacta de "redondee decimales": ¿entero hacia arriba (ceil, criterio de
    facturación de km), redondeo al entero más cercano, o fijar 2 decimales? ¿El redondeo es solo
    de presentación (formateo en la UI) o cambia el valor guardado en `kms_a_facturar` y lo que ve el
    motor (ALT002 compara con `cant_km_esperado` y tolerancia 0.5)? Distinta respuesta = distinto
    alcance (frontend solo vs dominio + migración de datos).
  - [P2] Qué es exactamente "más de un recorrido para la misma localidad": ¿misma empresa+sucursal+
    fecha, o cualquier par de incidentes del mismo día en la misma localidad de distinto cliente?
    ¿Umbral de distancia/km? ¿Es un campo VISUAL informativo en la pantalla de detalle (preferido por
    el "lo vamos viendo") o una Alerta/Observación real del motor? Confirmar si se puede reusar la
    lógica de corredor de ALT005/ALT003 en vez de una regla nueva.
  - [P3]/[P8] Qué es "web agentes" con precisión: URL base del portal AyC, si expone una URL estable
    por liquidación y con qué identificador (¿`numero_liquidacion`? ¿un id de AyC que hoy NO
    guardamos?). Definir el alcance real: (a) LINK — guardar/construir una URL y mostrar un botón "Abrir
    en web agentes" (barato, sin integración), vs (b) VÍNCULO CON DATOS — traer/empujar datos vía WS
    (caro, reabre todo lo que la caracterización §4 dejó afuera). El énfasis en mayúsculas de P8 sugiere
    que la prioridad es el link (a); confirmarlo.
  - [P4] Qué es el ítem "extra": ¿un campo/monto suelto a nivel liquidación, o una línea nueva por
    incidente? ¿Entra en `total_importe`/afecta el motor, o es informativo? ¿Categorías fijas (seguros,
    documentación, …) o texto libre? De esto depende si es columna nueva, tabla nueva, o entidad.
  Entregable: nota corta con la decisión por ítem, para anclar el diseño de las fases siguientes.

FASE 1 — Bajo riesgo, UI-acotado (P5, P6, P7). No depende de la Fase 0:
  - [P5] Extender `estado-badge.tsx` para colorear los 6 estados de liquidación (hoy solo 3) con
    variantes de `Badge` y tokens de marca dark-aware; evaluar también colorear los estados de
    observación en `observaciones-seccion.tsx`. Cosmético, sin backend.
  - [P6] Agregar dropdown de PERÍODO en la lista (ya existen los de prestador y estado). Mover el
    filtrado a server-side: extender `GET /api/liquidaciones` con `?periodo=` (y que el filtro de
    estado deje de ser client-side sobre la página, que hoy es un bug latente al paginar). Tocar el
    puerto `LiquidacionRepository` y el use case `list_liquidaciones` para aceptar los filtros; los
    valores de período salen de las liquidaciones existentes (distinct de `periodo`, formato "YYYY-MM").
  - [P7] Agregar selectores de PRESTADOR y AÑO en el dashboard para analizar costo. Derivar el año de
    `periodo`; recalcular los KPIs/agregados filtrando por prestador+año. Resolver el cap de 200 filas
    (que va a truncar) con un fetch paginado por total o un endpoint de stats agregado server-side —
    misma decisión que ya se tomó para tarifarios; no dejar truncado en silencio.

FASE 2 — Dominio/datos (P1, P2). Requiere las decisiones de la Fase 0:
  - [P1] Aplicar el redondeo según lo confirmado. Si es presentación: helper de formateo en
    `frontend/.../lib/format.ts` aplicado en las vistas de Tabla KM / incidentes. Si cambia el valor
    guardado: la regla vive en el use case de config de Tabla KM (`config_tabla_km.py`), nunca en el
    router ni en el repo directo; si hay que recalcular las 1633 filas ya cargadas, migración Alembic
    idempotente y verificada contra dato real, con impacto en ALT002 evaluado explícitamente.
  - [P2] Según Fase 0: si es campo VISUAL, derivarlo (sin persistir alerta) en el detalle reusando la
    lógica de corredor/localidad ya existente (`motor_reglas/_resolucion.py`) y mostrarlo en
    `incidentes-seccion.tsx`. Si es regla del motor, agregar el evaluador nuevo respetando el patrón
    (clase en `domain/services/motor_reglas/`, alta en el registro `EVALUADORES`, fila en `reglas_alerta`
    vía Alembic, tests de caracterización) y — a diferencia del legacy — sin `except Exception`
    silencioso (ARCHITECTURE_GUIDE §6).

FASE 3 — Web agentes (P3, P4, P8). Alcance que estaba excluido — máxima cautela:
  - [P8]/[P3] Si la Fase 0 confirma LINK (opción a): guardar o construir la URL a la liquidación en web
    agentes y exponer un botón/enlace en la pantalla de detalle y/o en la fila de la lista. Si hace
    falta persistir la referencia, columna nueva en `liquidaciones` (migración Alembic) escrita vía use
    case, nunca repo directo. Si la Fase 0 confirma VÍNCULO CON DATOS (opción b), NO se implementa a
    ciegas: se documenta primero un ADR de fuente/dirección de datos (como el 014) y se rediseña la
    política de conflictos — NUNCA heredar el delete+recreate del legacy que pisa el estado-workflow de
    la TL (caracterización §4).
  - [P4] Según Fase 0: agregar el ítem "extra" como el modelo que se haya decidido (columna en
    liquidación / línea por incidente / entidad nueva), con su ABM manual en la UI de detalle y toda
    escritura por use case de application. Si algún día se toma desde web agentes, que la carga manual
    quede como fallback (mismo criterio de convivencia que rige el resto del módulo).

[FORMATO]
- Todo texto a la TL/usuario en español de Argentina, directo, sin cortesías (regla de CLAUDE.md).
- Fase 0 se entrega como nota corta (una decisión por ítem) antes de escribir código de esas fases.
- Cambios de arquitectura no triviales (P3/P4 opción b, o P2 como regla nueva) → ADR numerado en
  `backend/docs/adr/` con el formato de los existentes (Estado/Contexto/Decisión/Consecuencias; ver
  012, 013, 014 como ejemplo).
- Código con commits atómicos en inglés siguiendo la convención del historial
  (`feat(liquidaciones): ...`), actualizando `LIQUIDACION_PRESTADORES_MIGRACION_ESTADO.md` al cierre de
  cada ítem.
- Al final de cada ítem: resumen de lo verificado con los comandos exactos corridos y su resultado real
  (no "debería pasar"), incluida la verificación visual en el navegador contra datos reales cuando el
  cambio sea de UI.

[RESTRICCIONES]
Operativas (innegociables, de CLAUDE.md):
- Antes de tocar o dejar correr cualquier código que dispare mails, SOAP o jobs de fondo:
  `DISABLE_BACKGROUND_JOBS=true` aplicado DE VERDAD (`docker compose up -d --force-recreate backend`,
  verificado con `printenv` y con el log de arranque — `docker restart` no relee `.env`). No reactivar
  jobs sin pedido explícito.
- Sin hot reload: tras editar backend `docker restart helpdesk-manager-backend`; tras editar frontend
  `docker restart helpdesk-manager-frontend` (re-corre `next build`, tarda). Verificar con `curl` antes
  de dar por servido un cambio; no confiar en la caché del navegador.
- Ninguna llamada real a web agentes / wsAyC que cree o modifique nada del lado de AyC. P3/P8 opción (a)
  es solo construir/guardar una URL; cualquier operación de escritura contra AyC queda fuera de alcance
  sin ADR y pedido explícito.
- No tocar el contenedor Docker de la app legacy ni su DB.

De arquitectura (ARCHITECTURE_GUIDE.md, verificadas antes de dar por terminado cada ítem):
- `uv run lint-imports` + `ruff check src tests` + `mypy src` + `pytest tests/unit -q` en verde dentro
  del contenedor backend; los tests de integración de liquidaciones corren desde el HOST
  (`localhost:5440`), no dentro del contenedor. Frontend: `tsc` + `eslint` + e2e Playwright en verde.
- Ningún `except Exception` silencioso (§6); todo endpoint que devuelva colección con envelope `Page[T]`
  (§11); archivo ≤300 líneas, clase ≤200, función ≤20 (§4); desviación consciente = ADR, no excepción
  tácita. Cuidado con `react-hooks/set-state-in-effect` en el frontend (ya mordió en este módulo:
  nada de `setState` síncrono en efectos ni en `catch` alcanzable desde un efecto — usar promise-chain).

De negocio:
- Toda escritura pasa por los use cases de application existentes; prohibido router→repo o →repo directo
  para escrituras (el recadenado de vigencias de tarifarios y la coherencia del modelo dependen de eso).
- El sync/carga automatizado nunca pisa datos editados a mano sin decisión explícita del usuario
  (aprender del riesgo de pisado documentado en la caracterización §4 y de la política del ADR-014).
- No inventar datos ni comportamiento: si un pedido no se puede resolver con evidencia (qué es "web
  agentes", qué identificador usa, qué significa "redondear"), el veredicto es "pendiente de la TL", no
  una suposición optimista.

[EJEMPLO]
Formato esperado de la nota de cierre de un ítem de Fase 1:

  [P5] Colores de estado — cerrado y verificado:
  - `estado-badge.tsx`: los 6 estados con variante/color propio (abierta=info, preliquidada=..., etc.),
    dark-aware, tokens de marca; observaciones coloreadas en `observaciones-seccion.tsx`.
  - tsc · eslint · 15 e2e Playwright en verde.
  - Verificación visual: lista y dashboard con los 6 estados distinguibles en claro y oscuro (captura).

Formato esperado del cierre de un ítem que toca dominio (Fase 2/3):

  [P1] Redondeo de kms a facturar — cerrado y verificado (decisión Fase 0: ceil, cambia valor guardado):
  - Regla en `config_tabla_km.py` (use case), no en router/repo. Migración `xxxx` recalculó N filas.
  - Impacto en ALT002 evaluado: reanalyze de la liquidación <id> → M alertas ALT002 (antes P), diff
    explicado.
  - lint-imports 17/17 · ruff · mypy · pytest unit (+K nuevos) · integración liquidaciones — en verde.
  - Dry-run/verificación contra dato real: <resultado exacto>.
```

---

## Notas de contexto para quien use este prompt (fuera del prompt en sí)

- **El pedido más caro y más ambiguo es "web agentes" (P3/P4/P8)**: reabre exactamente lo que la
  migración dejó afuera a propósito (WS AyC, caracterización §4/§6.1). El énfasis en mayúsculas de P8
  ("COLOCAR LINK DIRECTO") sugiere fuerte que lo que la TL quiere primero es un **enlace** para abrir la
  liquidación en el portal, no una integración de datos. Esa distinción (link vs vínculo con datos)
  cambia el esfuerzo de horas a semanas y es lo primero a confirmar en la Fase 0.
- **P5, P6 y P7 son los "quick wins"**: P5 es puramente cosmético; P6 y P7 son de UI pero arrastran dos
  bugs latentes reales que conviene cerrar de paso — el filtro de estado client-side sobre la página en
  la lista, y el cap de 200 filas del dashboard que va a truncar el análisis de costo cuando el
  histórico crezca. Si hay que entregar algo rápido, arrancar por acá.
- **P2 choca con "el motor es data-driven a medias"**: agregar una regla nueva es código (clase +
  registro `EVALUADORES` + fila en `reglas_alerta`), no un ajuste de config — lo confirma la
  caracterización §3. Pero el "lo vamos viendo" del pedido empuja a resolverlo primero como campo
  visual derivado (sin persistir alertas), reusando la lógica de corredor/localidad de ALT005/ALT003 que
  ya existe, antes de comprometerse a una regla formal.
- **P1 parece trivial y no lo es**: si "redondear" cambia el valor guardado de `kms_a_facturar`, toca el
  dato que ALT002 usa para validar km (tolerancia 0.5) y las 1633 filas ya cargadas — es una migración
  con impacto en el motor, no un `.toFixed(0)` en la vista. Por eso está en Fase 2 y detrás de la
  Fase 0.
