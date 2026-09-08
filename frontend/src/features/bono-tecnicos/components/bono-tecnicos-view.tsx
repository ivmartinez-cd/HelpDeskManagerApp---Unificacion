"use client";

import { Suspense } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { BonoGerenciaView } from "./gerencia/bono-gerencia-view";
import { BonoTecnicosDetail } from "./bono-tecnicos-detail";
import { useSession } from "@/services/session-provider";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { Spinner } from "@/shared/components/ui/spinner";

type Tab = "gerencia" | "carga";

/** /bono-tecnicos: vista de gerencia (evolución anual, lectura) por defecto,
 * y la carga mensual operativa como pestaña secundaria solo para quien puede
 * cargar Días o aprobar TV — mismo `SegmentedControl` + `?tab=` que
 * `turnos-admin-tabs.tsx`. */
function BonoTecnicosViewContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { user, can } = useSession();
  const puedeCargar =
    user.isSuperadmin || can("bono-tecnicos", "update") || can("bono-tecnicos", "approve");

  const tab: Tab = searchParams.get("tab") === "carga" && puedeCargar ? "carga" : "gerencia";

  if (!puedeCargar) {
    return <BonoGerenciaView />;
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="px-9 pt-6">
        <SegmentedControl
          label="Sección de Bono Técnicos"
          options={[
            { value: "gerencia", label: "Gerencia" },
            { value: "carga", label: "Carga mensual" },
          ]}
          value={tab}
          onChange={(v) => router.replace(v === "gerencia" ? pathname : `${pathname}?tab=${v}`)}
        />
      </div>
      {tab === "gerencia" ? <BonoGerenciaView /> : <BonoTecnicosDetail />}
    </div>
  );
}

export function BonoTecnicosView() {
  return (
    <Suspense
      fallback={
        <div className="flex justify-center p-8">
          <Spinner />
        </div>
      }
    >
      <BonoTecnicosViewContent />
    </Suspense>
  );
}
