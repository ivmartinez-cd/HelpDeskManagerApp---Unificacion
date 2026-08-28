/** Tipos del módulo Clientes: `GET /api/insumos/customers` y sub-endpoints.
 *
 * NOTA: el backend NO define `serialization_alias` en estos schemas, así que
 * los campos viajan en snake_case tal cual (`customer_id`, `has_contacts`,
 * `sol_apellido`, etc.). NO "corregir" a camelCase o los valores llegan
 * `undefined` en runtime. */

/** `CustomerOut`: cliente de Insight con flag de monitoreo habilitado. */
export interface CustomerRow {
  customer_id: number;
  name: string;
  enabled: boolean;
  has_contacts: boolean;
  /** Opt-in de aviso por mail al cliente cuando se carga su pedido — apagado por
   * default en toda la cartera. */
  client_mail_enabled: boolean;
}

/** `ZoneContactOut`: contacto completo de una zona de un cliente.
 * Unicidad por `(customer_id, zone)` en la BD; el zone es la PK lógica. */
export interface ZoneContactRow {
  zone: string;
  sol_apellido: string;
  sol_nombre: string;
  sol_telefono: string;
  sol_email: string;
  sol_sector: string;
  dest_apellido: string;
  dest_nombre: string;
  dest_telefono: string;
  dest_email: string;
  dest_sector: string;
  observaciones: string;
}

/** `SdsContactOut`: contacto detectado en el PortalWeb de SDS (solo lectura,
 * piloto para un subconjunto de clientes). */
export interface SdsContactRow {
  zone: string;
  contacto: string;
  email: string;
  sucursal: string;
}

export interface SyncCustomersResponse {
  ok: boolean;
  count: number;
}

/** `ImportContactsResponse`: resultado de importar el contacto de una zona
 * desde un pedido de supply (SOAP HP SDS, upsert directo sin preview). */
export interface ImportFromSupplyResponse {
  ok: boolean;
  zone?: string | null;
  row?: ZoneContactRow | null;
  error?: string | null;
}

/** `ZoneContactPreviewRowOut`: una fila del preview de importación masiva
 * desde el PortalWeb de SDS, con el valor entrante y el actual en paralelo
 * para poder armar una tabla-diff. */
export interface ZoneContactPreviewRow {
  zone: string;
  apellido: string;
  nombre: string;
  email: string;
  telefono: string;
  already_configured: boolean;
  error: string | null;
  current_apellido: string;
  current_nombre: string;
  current_email: string;
  current_telefono: string;
}

export interface ZoneContactPreviewResponse {
  ok: boolean;
  rows: ZoneContactPreviewRow[];
  error?: string | null;
}

/** `ZoneContactApplyRowIn`: fila seleccionada para aplicar. `overwrite` va en
 * `true` cuando la zona ya estaba configurada (no hay checkbox separado en la
 * UI — seleccionar una fila `already_configured` implica pisarla). */
export interface ZoneContactApplyRow {
  zone: string;
  overwrite: boolean;
}

export interface ZoneContactApplyResponse {
  ok: boolean;
  applied: number;
  error?: string | null;
}
