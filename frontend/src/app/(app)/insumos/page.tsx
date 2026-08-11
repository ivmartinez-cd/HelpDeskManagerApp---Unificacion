"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { InsumosDashboard } from "@/features/insumos/components/dashboard/insumos-dashboard";
import { Spinner } from "@/shared/components/ui/spinner";

/** Dashboard de Insumos (`/insumos`). El módulo NO tiene hub de herramientas:
 * `/insumos` es directamente el Dashboard.
 *
 * `useSearchParams` obliga a un `<Suspense>` alrededor (mismo patrón que
 * `contadores/page.tsx`): sin él, Next.js falla el build estático de la ruta.
 * El deep-link `?customerId=123` llega desde los avisos de solicitudes sin
 * cargar y expande ese cliente apenas carga la tabla. */
function InsumosDashboardContent() {
  const searchParams = useSearchParams();
  const raw = searchParams.get("customerId");
  const customerId = raw === null ? null : Number(raw);

  return (
    <InsumosDashboard
      deepLinkCustomerId={customerId !== null && Number.isFinite(customerId) ? customerId : null}
    />
  );
}

export default function InsumosDashboardPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-64 items-center justify-center">
          <Spinner />
        </div>
      }
    >
      <InsumosDashboardContent />
    </Suspense>
  );
}
