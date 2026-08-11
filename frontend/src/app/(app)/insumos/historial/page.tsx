"use client";

import { Suspense } from "react";
import { HistorialView } from "@/features/insumos/components/historial/historial-view";
import { Spinner } from "@/shared/components/ui/spinner";

/** Historial de Insumos (`/insumos/historial`).
 *
 * La pantalla lee la pestaña activa de `?tab=` con `useSearchParams()`, que
 * obliga a un límite de Suspense arriba (mismo patrón que
 * `app/(app)/contadores/page.tsx`): sin él, Next no puede prerenderizar la
 * ruta. */
export default function InsumosHistorialPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-64 items-center justify-center">
          <Spinner />
        </div>
      }
    >
      <HistorialView />
    </Suspense>
  );
}
