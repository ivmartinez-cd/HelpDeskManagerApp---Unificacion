"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { AcuerdosConfig } from "@/features/liquidaciones/components/acuerdos-config";
import { Spinner } from "@/shared/components/ui/spinner";

/** El deep-link `?prestadorId=&empresa=&tipo=&cobrado=` llega desde una
 * alerta ALT001 del detalle ("Cargar acuerdo para este cliente") y precarga el
 * alta. `useSearchParams` obliga a un `<Suspense>` (mismo patrón que
 * tarifarios/page.tsx). */
function AcuerdosConfigContent() {
  const sp = useSearchParams();
  const prestadorId = sp.get("prestadorId");
  const empresa = sp.get("empresa");
  return (
    <AcuerdosConfig
      deepLink={
        prestadorId && empresa
          ? { prestadorId, empresaNombre: empresa, tipoServicio: sp.get("tipo") ?? "", cobrado: sp.get("cobrado") ?? "" }
          : null
      }
    />
  );
}

export default function AcuerdosConfigPage() {
  return (
    <Suspense fallback={<div className="flex h-64 items-center justify-center"><Spinner /></div>}>
      <AcuerdosConfigContent />
    </Suspense>
  );
}
