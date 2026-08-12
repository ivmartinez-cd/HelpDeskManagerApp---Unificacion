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
