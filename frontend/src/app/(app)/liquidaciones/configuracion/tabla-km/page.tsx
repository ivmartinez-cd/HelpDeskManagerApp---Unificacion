"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { TablaKmConfig } from "@/features/liquidaciones/components/tabla-km-config";
import { Spinner } from "@/shared/components/ui/spinner";

/** `useSearchParams` obliga a un `<Suspense>` alrededor (mismo patrón que
 * `insumos/page.tsx`). Dos deep-links posibles, ambos desde el detalle de
 * liquidación: `?prestadorId=&empresa=&sucursal=` (incidente "Sin tabla" — no
 * hay fila de Tabla KM, precarga el alta) y `?prestadorId=&buscar=` (alerta
 * ALT008/ALT009 sin SPST resuelto — la fila ya existe pero le falta el SPST,
 * precarga el buscador para que la encuentres y la edites). */
function TablaKmConfigContent() {
  const searchParams = useSearchParams();
  const prestadorId = searchParams.get("prestadorId");
  const empresa = searchParams.get("empresa");
  const sucursal = searchParams.get("sucursal");
  const buscar = searchParams.get("buscar");

  return (
    <TablaKmConfig
      deepLinkFaltante={
        prestadorId && empresa && sucursal ? { prestadorId, empresa, sucursal } : null
      }
      deepLinkBuscar={prestadorId && buscar ? { prestadorId, query: buscar } : null}
    />
  );
}

export default function TablaKmConfigPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-64 items-center justify-center">
          <Spinner />
        </div>
      }
    >
      <TablaKmConfigContent />
    </Suspense>
  );
}
