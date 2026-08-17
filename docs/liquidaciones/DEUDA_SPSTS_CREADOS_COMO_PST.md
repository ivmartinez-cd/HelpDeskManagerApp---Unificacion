# Deuda técnica — SPSTs heredados del legacy con nombre "PST ..."

> **Estado 2026-08-17: SANEADA en la DB de dev.** El dry-run de
> `backend/scripts/limpiar_spsts_pst_legacy.py` contra `helpdesk` reporta **0 SPSTs con
> prefijo "PST "** (quedan 15 SPSTs, todos legítimos). El script queda en el repo para
> re-verificar en cualquier entorno (dry-run por default; `--apply` implementa la
> propuesta de este doc si la deuda reaparece, p. ej. tras re-sembrar desde otro backup).

Fecha de análisis: 2026-08-16. Datos de `helpdesk` (sembrada desde producción el 2026-08-13).

## El problema

El legacy (SQLite de `liquidacion-prestadores`) creaba automáticamente un SPST "genérico"
para cada PST al momento de la carga inicial. Ese SPST representaba al **PST mismo** (su
base de despacho principal), no a un sub-prestador real con base propia diferente. La
convención de nombre que eligió el legacy fue la misma que usa Siges para la entidad PST:
prefijo `"PST "` (ej. `"PST Mendoza - System&Print"`). Resultado: **35 SPSTs en la DB
local cuyos nombres empiezan con `"PST "` o `"PST PST "` (doble prefijo, artefacto de la
migración del snapshot)**.

En Siges (`dbo.Empresa`), esas entidades tienen el prefijo `"PST "` —
son PSTs en Siges, no SPSTs. El sync de ADR-014 distingue PSTs de SPSTs por prefijo
(`_tipo()` en el gateway) y solo busca entidades `"SPST%"` al vincular SPSTs locales,
así que **ninguno de estos 35 quedó vinculado a Siges** durante la sincronización.

## Inventario completo

### SPSTs "PST" con filas de Tabla KM (impacto real en routing)

| PST | SPST local | Filas KM | `siges_base_sucursal_id` |
|---|---|---:|---|
| BAHIA | PST PST Bahia Blanca - Eduardo Lledos | 15 | — |
| CDU | PST PST Concepción del Uruguay - Javier Argachá | 43 | — |
| CHACO | PST PST Chaco - Asesores Informaticos | 29 | — |
| JUJUY | PST Jujuy - Alfredo Espinoza | 24 | — |
| MACARONE | PST PST Parana - Macarone Ariel | 99 | — |
| MDQ | PST PST Mar del Plata - Jose Luis Bortolazzi | 102 | — |
| MENDOZA | PST Mendoza - System&Print | 108 | — |
| PENTACOM | PST Córdoba - Pentacom S.A. | 188 | — |
| PERGAMINO | PST PST Pergamino - Copiers Fotocopiadoras | 32 | — |
| SM TUCUMAN | PST SM Tucuman - Leonardo Herculano | 33 | — |
| SAN JUAN | PST San Juan - Gestión Integral | 487 | **2649** (= base del PST SAN JUAN) |
| SUPERNOVA | PST Rosario - Supernova | 193 | — |
| VENADO | PST PST Venado Tuerto - Natali Servicios | 30 | — |

**Total: 1.383 filas de Tabla KM** apuntando a SPSTs del legacy que no son
sub-prestadores reales.

### SPSTs "PST" sin filas de Tabla KM (sin impacto inmediato)

CALETA, CATAMARCA, CHACABUCO, CHIVILCOY, COMODORO, CORRIENTES, FORMOSA, JUNIN,
LA RIOJA, OLAVARRIA, POSADAS, RIO GALLEGOS, RIO GRANDE, SALTA, SAN LUIS, SAN RAFAEL,
TANDIL, TRELEW, TUCUMAN, VIEDMA — 20 PSTs, 0 filas KM cada uno.

### Casos especiales con duplicados

**MENDOZA** tiene dos SPSTs "PST" para el mismo prestador:

| Nombre | Filas KM |
|---|---:|
| PST Mendoza - System&Print | 108 |
| PST PST Mendoza - System&Print | 0 |

El primero es el activo real; el segundo es una importación con doble prefijo.

**PENTACOM** tiene dos SPSTs "PST Córdoba" que difieren solo en la tilde:

| Nombre | Filas KM |
|---|---:|
| PST Córdoba - Pentacom S.A. | 188 |
| PST Cordoba - Pentacom S.A. | 3 |

El de tilde es el activo real; el sin tilde es un duplicado de la migración.

### SPST redundante por `siges_base_sucursal_id` (pendiente #5 del estado doc)

`PST San Juan - Gestión Integral` tiene `siges_base_sucursal_id = 2649`, que coincide
con el `siges_base_sucursal_id` del PST SAN JUAN. `RecalcularKmFila` resolvería la misma
base (2649) con o sin SPST. Las 487 filas deberían apuntar a `spst_id = NULL`.

SAN JUAN sí tiene un SPST legítimo: `GSJ - Escuelas Valle Fértil`
(`siges_base_sucursal_id = 14549`, base diferente, zona Valle Fértil). Ese queda intacto.

## Impacto funcional actual

**Sin impacto en el cálculo de km** para los 34 SPSTs sin `siges_base_sucursal_id`:
`RecalcularKmFila` y el batch preview resuelven la base así:

```
1. SPST tiene siges_base_sucursal_id → usa las coords de esa sucursal
2. Si no → usa la base default del PST (siges_base_sucursal_id del PST padre)
```

Como ninguno de los 34 tiene `siges_base_sucursal_id`, todos caen al caso 2 y usan la
base del PST, que es exactamente el comportamiento correcto. El único con impacto real
es SAN JUAN (caso 1 con base redundante, resultado igual al caso 2).

**Impacto en UX**: la pantalla de SPSTs muestra estos 35 registros mezclados con los
SPSTs reales (INFOMAC, PENTACOM, SUPERNOVA), haciendo que la lista sea confusa.

**Impacto en sync Siges**: ninguno de estos 35 puede vincularse a una entidad "SPST"
de Siges porque en Siges son entidades con prefijo "PST ". Si algún día se necesita
vincular la base del PST a una sucursal propia de Siges, el vínculo correcto es
configurar `siges_base_sucursal_id` en el **PST** (ya existe el campo y el endpoint
`PUT /prestadores/{id}/siges-base-sucursal`), no en el SPST genérico.

## Acción propuesta

Para cada uno de estos SPSTs, en orden de prioridad por volumen de filas:

1. **Reasignar filas de Tabla KM** del SPST "PST" a `spst_id = NULL` (o al SPST
   legítimo correcto si el PST tiene uno).
   - Excepción PENTACOM: las 3 filas de "PST Cordoba" (sin tilde) deben reasignarse
     a "PST Córdoba" (con tilde), no a NULL, para no perder el routing de sub-zona.
2. **Eliminar el SPST** por `DeleteSpst` (cascade a tabla KM ya reasignada → no hay
   filas que borrar en cascada).
3. **No configurar** `siges_base_sucursal_id` en estos SPSTs antes de eliminarlos —
   el campo correcto donde configurar la base del PST ya existe en `prestadores`.

### PSTs con SPSTs legítimos que conviven con el "PST" genérico

Antes de reasignar a NULL, verificar si las filas del SPST "PST" deben ir a un SPST
legítimo o a NULL según el ruteo geográfico:

- **SAN JUAN**: las 487 filas de "PST San Juan - Gestión Integral" van a `spst_id = NULL`
  (base 2649 del PST es la correcta para esas sucursales; "GSJ" con base 14549 es para
  sucursales del Valle Fértil, diferente zona).
- **SUPERNOVA**: las 193 filas de "PST Rosario - Supernova" van a `spst_id = NULL`
  (la base del PST es Rosario). SUPERNOVA sí tiene SPSTs legítimos (Rafaela, Santa Fe)
  pero son sub-zonas distintas.

## Decisiones que requieren confirmación de la TL

Antes de ejecutar la remediación:

1. ¿El criterio de reasignación es siempre `NULL` (base del PST) o hay casos donde
   las filas del SPST "PST" deberían ir a un SPST legítimo diferente?
2. PENTACOM: ¿las 3 filas de "PST Cordoba" (sin tilde) van a "PST Córdoba" (con tilde)
   o a NULL?
3. ¿Priorizar la remediación por volumen (SAN JUAN 487, SUPERNOVA 193, PENTACOM 191)
   o hacerla en bloque en una sola sesión?

## No confundir con

**SPSTs del legacy sin prefijo PST** (PENTACOM: "Laboulaye - Roberto Gil",
"Pentacom - Arroyito"): estos también son artefactos del legacy (nombres sin prefijo),
pero tienen duplicados modernos con prefijo "SPST " que los reemplazan. Son una deuda
separada de limpieza de duplicados, no de la confusión PST/SPST.
