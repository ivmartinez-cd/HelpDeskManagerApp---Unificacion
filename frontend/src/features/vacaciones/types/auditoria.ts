export interface RegistroAuditoria {
  id: string;
  accion: string;
  entidad: string;
  entidadId: string | null;
  usuarioEmail: string | null;
  metadata: Record<string, unknown>;
  createdAt: string;
}

/** Columnas por las que el backend ordena el log (`sort_by`). Descripción no
 * está: se arma en el navegador a partir de la metadata. */
export type AuditoriaSortKey = "fecha" | "accion" | "entidad" | "usuario";
