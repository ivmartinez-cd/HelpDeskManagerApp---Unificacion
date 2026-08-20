# ADR-027: `CD_ORIGEN_ID` pasa de 3 (Interno) a 6 (Proactivo)

## Estado: Aceptado

## Contexto

La migración de `insumos` a SOAP (crear pedidos vía `persistNewSupply` en vez de scrapear
el portal) usó desde el principio `origen_id = 3` (Interno): era el único valor disponible
para distinguir los pedidos automáticos de esta app de los cargados a mano en el portal
(el formulario HTML siempre dejaba el origen en Web).

Esa elección tuvo un costo operativo real, confirmado leyendo el código fuente del
servicio (`WebService-AyC/app/wsAyC_server.php`): `getTopSupplies` filtra explícitamente
`WHERE ... AND i.ID_Origen <> 3`. Todo pedido que crea esta app queda **invisible en AyC y
en el listado del portal de Canal Directo** — los agentes no lo ven en su herramienta
habitual. El legacy SDSInsumos convivió con esto compensando con un scan incremental de
IDs (`supply_scanner.py`) que el monorepo nunca portó (ver `SDSINSUMOS_MIGRACION_ESTADO.md`,
"Decisión 2026-08-11: scan incremental descartado por ahora").

Canal Directo dio de alta un origen nuevo, **Proactivo (`ID_Origen = 6`)**, exclusivo para
la carga automática de esta app. El filtro del servicio sigue excluyendo solo `3`, así que
los pedidos con origen 6 sí atraviesan `getTopSupplies`, AyC y el listado del portal.

## Decisión

`CD_ORIGEN_ID` pasa de `3` a `6` (default en `settings.py`, `.env`, `.env.example`),
parametrizable por variable de entorno para rollback sin redeploy.

El cambio alcanza a **ambos** flujos que comparten `CanalDirectoOrderSettings.origen_id`:
los pedidos de insumos (`order_creation.py`, SOAP `persistNewSupply`) y los incidentes
Pre-Correctivo de kits de mantenimiento (`incident_creation.py`, SOAP `persistNewIncident`).

## Qué NO cambia

- El mecanismo de creación es idéntico: `origen_id` sigue viajando en la raíz del payload
  de `persistNewSupply` además de anidado en `Supply` (`order_creation.py`, con test de
  regresión — es el bug real que corrigió el legacy: `wsAyC_server.php` lee
  `$supply['origen_id']` de la raíz, no solo de `Supply`).
- El cache local `supply_serial_cache` **sigue siendo necesario**, aunque ya no por el
  motivo original ("es la única vía que ve los pedidos propios"). El gate anti-duplicados
  en creación (`CanalDirectoSupplyLookup` / `find_active_supply_by_serial`) solo consulta
  el cache local, nunca llama a `getTopSupplies` en vivo. Sin el seed inmediato al crear
  (`order_creation.py::_seed_cache`), un pedido recién creado con origen 6 quedaría
  invisible para ese gate hasta el próximo ciclo de un scan que este módulo no tiene
  portado — la misma ventana de duplicado que existía con origen 3.
- Los pedidos ya creados con origen 3 (si los hubiera en dev, sembrados desde el backup de
  producción) no se migran retroactivamente: siguen invisibles en `getTopSupplies` mientras
  estén activos. Sin scan portado, el monorepo no tiene forma de verlos por ID — punto ciego
  aceptado, ya existente antes de este cambio.

## Efecto sobre el placeholder consciente del supply-scan

El módulo `insumos` nunca portó `supply_scanner.py` (scan incremental de IDs por
`getSupplyById`, la única vía que veía pedidos con origen Interno). Con origen Proactivo,
los pedidos **propios** nuevos pasan a ser visibles directo por `getTopSupplies`, así que el
punto ciego que dejaba el scan sin portar se cierra **para pedidos propios**. Sigue abierto
para: (a) el remanente histórico con origen 3, y (b) pedidos de "Origen Interno" cargados
por fuera de la app (ver memoria de sesión sobre el estado de la migración) — ninguno de los
dos motivos cambia con este ADR.

## Consecuencias

- Los pedidos e incidentes creados desde ahora son visibles para los agentes en AyC y en el
  portal, sin depender de un scan que no existe en este módulo.
- Rollback disponible sin redeploy: `CD_ORIGEN_ID=3` en `.env` + recrear el contenedor
  (`docker compose up -d --force-recreate backend` — `docker restart` no relee `.env`).
