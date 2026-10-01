/** Solo se renderiza como link lo que es http(s): en la tabla de km hay valores
 * cargados a mano ("maps", direcciones sin esquema) y cualquier otro esquema no
 * tiene que llegar a un href (auditoría de seguridad 2026-09-30). */
export function esUrlWeb(valor: string | null | undefined): valor is string {
  return !!valor && /^https?:\/\//i.test(valor.trim());
}
