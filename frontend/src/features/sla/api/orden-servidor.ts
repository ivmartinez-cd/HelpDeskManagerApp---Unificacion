/** Orden por columna que se manda a los listados paginados de SLA
 * (`sort_by`/`sort_dir`): el backend ordena la lista completa antes de
 * cortar la página. Sin `sortBy` rige el orden de negocio del endpoint. */
export interface OrdenServidor {
  sortBy?: string;
  sortDir?: "asc" | "desc";
}

export function aplicarOrden(params: URLSearchParams, orden?: OrdenServidor): URLSearchParams {
  if (orden?.sortBy) {
    params.set("sort_by", orden.sortBy);
    params.set("sort_dir", orden.sortDir ?? "asc");
  }
  return params;
}
