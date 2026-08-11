import { NewDevicesView } from "@/features/insumos/components/equipos-nuevos";

export const metadata = { title: "Equipos nuevos · Insumos" };

/** `/insumos/equipos-nuevos` — listado de equipos sin monitorear
 * (`/api/insumos/new-devices`), con sync manual contra Insight y toggle de
 * ignorar/restaurar. Toda la interacción vive en el componente cliente. */
export default function InsumosEquiposNuevosPage() {
  return <NewDevicesView />;
}
