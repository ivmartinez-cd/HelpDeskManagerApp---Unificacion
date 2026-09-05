"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { TarifariosConfig } from "@/features/liquidaciones/components/tarifarios-config";
import { Spinner } from "@/shared/components/ui/spinner";

/** `useSearchParams` obliga a un `<Suspense>` alrededor (mismo patrón que
 * `insumos/page.tsx` y `tabla-km/page.tsx`). El deep-link
 * `?prestadorId=&tipoServicio=&spstId=` llega desde una alerta ALT008 ("Sin
 * tarifario") en el detalle de liquidación y precarga el alta de la tarifa
 * faltante. */
function TarifariosConfigContent() {
  const searchParams = useSearchParams();
  const prestadorId = searchParams.get("prestadorId");
  const tipoServicio = searchParams.get("tipoServicio");
  const spstId = searchParams.get("spstId");

  return (
    <TarifariosConfig
      deepLinkFaltante={
        prestadorId && tipoServicio ? { prestadorId, tipoServicio, spstId: spstId ?? "" } : null
      }
    />
  );
}

export default function TarifariosConfigPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-64 items-center justify-center">
          <Spinner />
        </div>
      }
    >
      <TarifariosConfigContent />
    </Suspense>
  );
}
