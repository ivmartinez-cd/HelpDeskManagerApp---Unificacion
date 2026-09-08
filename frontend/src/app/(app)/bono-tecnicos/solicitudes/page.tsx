import { redirect } from "next/navigation";

/** Ruta vieja de "Mis Tareas Varias", de antes del split del módulo
 * `tareas_varias` — se mantiene solo para no romper links/bookmarks. */
export default function MisSolicitudesTvRedirectPage() {
  redirect("/tareas-varias");
}
