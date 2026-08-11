"use client";

import { Suspense, use } from "react";
import { ClienteEstadisticas } from "@/features/insumos/components/estadisticas/cliente-estadisticas";
import { Spinner } from "@/shared/components/ui/spinner";

/** Detalle de cliente en Estadísticas
 * (`/insumos/estadisticas/clientes/[id]`).
 *
 * `params` llega como Promise y se desenvuelve con `use()` — misma convención
 * que `app/(app)/admin/usuarios/[id]/permisos/page.tsx`. El rango de fechas se
 * lee del querystring, así que la vista va debajo de un `<Suspense>`. */
export default function InsumosEstadisticasClientePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  return (
    <Suspense
      fallback={
        <div className="flex h-64 items-center justify-center">
          <Spinner />
        </div>
      }
    >
      <ClienteEstadisticas id={id} />
    </Suspense>
  );
}
