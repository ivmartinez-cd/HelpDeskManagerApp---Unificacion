/** Tipos transversales del módulo Insumos.
 *
 * REGLA GENERAL DE ESTE DIRECTORIO: cada interfaz refleja **exactamente** el
 * schema que publica el backend en `/api/openapi.json` (módulo `insumos`), con
 * los nombres de campo tal cual viajan por la red. El backend serializa casi
 * todo en camelCase vía `serialization_alias`, pero hay tres schemas que
 * quedaron en snake_case (`AuditRowOut`, `MailLogRowOut`, `DeviceSupplyItemOut`)
 * — están tipados en snake_case a propósito, no "corregir" a camelCase o el
 * dato llega `undefined` en runtime.
 *
 * Las fechas viajan como string ISO 8601 (`format: date-time`) o `YYYY-MM-DD`
 * (`format: date`); acá se tipan como `string` y se formatean con los helpers
 * de `../utils/format.ts`, que fuerzan huso horario Argentina como el legacy.
 */

export type { DateRange } from "@/shared/types/date-range";
