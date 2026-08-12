import { ClientesView } from "@/features/insumos/components/clientes";

export const metadata = { title: "Clientes · Insumos" };

/** `/insumos/clientes` — gestión de clientes monitoreados: habilitar/deshabilitar
 * monitoreo por cliente y editar contactos por zona
 * (`/api/insumos/customers` y sub-endpoints). */
export default function InsumosClientesPage() {
  return <ClientesView />;
}
