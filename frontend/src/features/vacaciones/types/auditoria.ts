export interface RegistroAuditoria {
  id: string;
  accion: string;
  entidad: string;
  entidadId: string | null;
  usuarioEmail: string | null;
  metadata: Record<string, unknown>;
  createdAt: string;
}
