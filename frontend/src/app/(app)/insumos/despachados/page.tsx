import { DespachadosView } from "@/features/insumos/components/despachados/despachados-view";

export const metadata = { title: "Despachados · Insumos" };

/** Insumos > Despachados (`/insumos/despachados`): seguimiento de los envíos
 * por OCA. La pantalla no lee `searchParams`, así que no necesita un límite de
 * Suspense (a diferencia de `historial/page.tsx`). */
export default function InsumosDespachadosPage() {
  return <DespachadosView />;
}
