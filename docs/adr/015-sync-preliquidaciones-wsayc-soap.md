# ADR-015: wsAyC SOAP como fuente de importación automática de preliquidaciones

## Estado: Aceptado e implementado (2026-08-13 — ver `docs/liquidaciones/LIQUIDACION_PRESTADORES_MIGRACION_ESTADO.md`)

## Contexto

ADR-014 eligió SigesReadOnly como fuente de sync para los tres datasets de
**configuración** (prestadores/SPSTs, tarifarios, tabla KM) y dejó wsAyC
explícitamente fuera con esta nota:

> *El import de preliquidaciones por wsAyC (el objetivo real de la rama legacy) queda
> explícitamente fuera: antes exige diseñar la reconciliación estado-TL vs estado-AyC
> (hoy una sola columna `estado`) que la caracterización §4 marca como no resuelta.*

La preocupación de §4 era el anti-patrón del legacy `feature/ws-ayc-liquidaciones`:
el sync reimportaba borrando y recreando la liquidación con cascade, perdiendo
observaciones y el estado de revisión de la TL. No había reconciliación — solo
reemplazo destructivo.

Este ADR resuelve esa preocupación con una política radicalmente más conservadora:
**el sync es aditivo puro** — crea liquidaciones inexistentes, nunca modifica ni
borra las existentes. Con esta restricción, la "reconciliación" es trivial y sin
riesgo: si `numero_liquidacion` ya está en la DB, se saltea.

### Observaciones técnicas que motivaron el diseño de la implementación

`getTopLiquidations(IdEmpresa="", Top=500)` no incluye `prestador_id` en su
respuesta — solo el nombre en texto libre (`Prestador: "PST Jujuy - Alfredo
Espinoza"`). Llamar sin filtro de empresa y luego intentar parsear el prestador
por nombre no es viable (texto libre, sin garantía de unicidad, distinto del nombre
local). La única forma de saber a qué prestador pertenece cada liquidación sin un
`getLiquidationById` adicional por item (500 llamadas extra para Top=500) es
filtrar **por empresa desde el origen**: `getTopLiquidations(IdEmpresa=str(cd_id))`.

Esto implica un vínculo persistente entre cada prestador local y su ID numérico en
wsAyC (`cd_prestador_id`), análogo a `siges_empresa_id` del ADR-014.

## Decisión

**wsAyC es la fuente de importación de preliquidaciones**, con las siguientes
restricciones que descartan el riesgo del §4:

1. **Aditivo puro**: `SincronizarLiquidaciones` compara el resultado del SOAP contra
   el SET de `numero_liquidacion` ya presentes en la DB. Si ya existe, se cuenta como
   `ya_existentes` y no se toca — el estado de revisión de la TL, las observaciones y
   los campos extra no corren riesgo en ningún caso.

2. **Por empresa, no global**: cada prestador con `cd_prestador_id` configurado
   recibe una llamada independiente `getTopLiquidations(IdEmpresa=str(cd_prestador_id))`.
   Esto elimina la ambigüedad de matching por nombre y evita el problema de `prestador_id`
   ausente en la respuesta global.

3. **`cd_prestador_id` como vínculo explícito**: campo nullable UNIQUE en `prestadores`
   (migración `d6e3c1b4a829`). El vínculo se establece una sola vez desde la pantalla
   de configuración (`PATCH /prestadores/{id}/vincular-cd`); el sync en runtime nunca
   hace matching por nombre.

4. **`getLiquidationDetails` solo para las nuevas**: los incidentes de cada liquidación
   nueva se obtienen con una segunda llamada SOAP. Liquidaciones ya existentes no generan
   ninguna llamada adicional — el costo SOAP es proporcional a lo verdaderamente nuevo.

5. **Sin dry-run**: dado que el sync es aditivo puro (nunca pisa), el dry-run no tiene
   valor de protección. El resultado (`creadas`, `yaExistentes`) ya es informativo.

6. **Estado inicial `abierta`**: mismo que el import CSV/Excel manual. La TL gestiona
   el workflow de estados desde ahí; el sync no asume ni fuerza ningún estado de
   revisión.

7. **Disparo manual** vía botón en el dashboard (`POST /api/liquidaciones/sincronizar`,
   requiere permiso `CREATE`). Sin job de fondo en esta iteración — si algún día se
   automatiza, requiere ADR propio y respeta `DISABLE_BACKGROUND_JOBS`.

8. **`ReanalizarLiquidacion` automático** al crear: cada liquidación nueva pasa por el
   motor de reglas antes de persistir el resultado. Mismo comportamiento que el import
   CSV/Excel.

### Por qué no SigesReadOnly para preliquidaciones

Siges (`dbo.Liquidacion`) existe pero no fue validado con dato real en la Fase 1 del
ADR-014 — se dejó como "tablas con nombre prometedor pero sin validar". wsAyC, en
cambio, fue validado: `getLiquidationDetails(3876)` devolvió los 111 incidentes de la
liquidación local `3876-6` con las mismas columnas del CSV que sube la TL. La paridad
está demostrada; la de Siges no.

## Consecuencias

- **Positivas**: el import de preliquidaciones pasa a ser un click desde el dashboard
  en lugar de un upload manual de CSV/Excel por prestador por mes; el histórico
  completo (no solo el mes actual) está disponible desde el primer sync; los incidentes
  importados son los mismos que vería la TL en web agentes; el motor de reglas corre
  automáticamente sobre cada liquidación nueva.

- **Negativas / limitaciones asumidas**:
  - El SOAP no garantiza que `Top=200` devuelva solo las liquidaciones más recientes
    (la API retorna las 200 en algún orden determinado por AyC, no necesariamente por
    fecha desc). En la práctica, para prestadores con muchas liquidaciones históricas,
    el primer sync puede traer datos muy antiguos. Aceptable: son datos reales de
    producción de AyC, correctos por definición.
  - El campo `estado` del SOAP no se mapea — la liquidación nace `abierta`
    independientemente de su estado en AyC. Si la TL necesita el estado real de AyC
    en el futuro, requiere extensión de este sync (nuevo campo o nueva llamada).
  - Dependencia de disponibilidad de wsAyC: si el SOAP no responde, el sync devuelve
    `[]` para ese prestador y loguea el error; las liquidaciones ya importadas no se
    ven afectadas.
  - La sync no descarta liquidaciones de `ZZTESTUI` ni de prestadores sin
    `cd_prestador_id` — simplemente nunca los itera (`list_con_cd_id()` los excluye).

- **Import CSV/Excel se mantiene intacto**: convive como fallback y como mecanismo
  para importar liquidaciones de prestadores sin `cd_prestador_id` (si alguna vez
  hubiera uno). No se retira hasta que el sync acumule un período de convivencia
  validado por la TL.
