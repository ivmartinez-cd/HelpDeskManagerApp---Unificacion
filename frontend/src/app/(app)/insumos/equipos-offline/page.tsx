import { OfflineDevicesView } from "@/features/insumos/components/equipos-offline";

export const metadata = { title: "Equipos offline · Insumos" };

/** `/insumos/equipos-offline` — equipos sin reportar +72hs, candidatos a baja
 * en SDS tras verificación contra Canal Directo. Toda la interacción vive en el
 * componente cliente. */
export default function InsumosEquiposOfflinePage() {
  return <OfflineDevicesView />;
}
