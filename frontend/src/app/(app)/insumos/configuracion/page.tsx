import { ConfiguracionView } from "@/features/insumos/components/configuracion";

export const metadata = { title: "Configuración · Insumos" };

/** `/insumos/configuracion` — parámetros de operación
 * (`GET`/`PUT /api/insumos/config`) en el formulario multi-sección del
 * Patrón 5. Toda la interacción vive en el componente cliente. */
export default function InsumosConfiguracionPage() {
  return <ConfiguracionView />;
}
