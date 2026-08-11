"use client";

import { Suspense } from "react";
import { EstadisticasGlobales } from "@/features/insumos/components/estadisticas/estadisticas-globales";
import { Spinner } from "@/shared/components/ui/spinner";

/** Estadísticas globales de Insumos (`/insumos/estadisticas`).
 *
 * El rango de fechas vive en el querystring (`start_date`/`end_date`), así que
 * la vista usa `useSearchParams()` y tiene que ir debajo de un `<Suspense>` —
 * mismo patrón que `app/(app)/contadores/page.tsx`. */
export default function InsumosEstadisticasPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-64 items-center justify-center">
          <Spinner />
        </div>
      }
    >
      <EstadisticasGlobales />
    </Suspense>
  );
}
