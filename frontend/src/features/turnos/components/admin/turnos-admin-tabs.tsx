"use client";

import { Suspense } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { CasillasManager } from "./casillas-manager";
import { ModoVacacionesView } from "../modo-vacaciones/modo-vacaciones-view";
import type { PrecargaInicial } from "../modo-vacaciones/variante-editor";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { Spinner } from "@/shared/components/ui/spinner";

const TABS = [
  { value: "titular", label: "Grilla titular" },
  { value: "vacaciones", label: "Modo vacaciones" },
];

type Tab = "titular" | "vacaciones";

/** /turnos: grilla titular (casillas/franjas/enroque) y modo vacaciones
 * (ADR-025) como pestañas — mismo SegmentedControl que el dashboard de Inicio.
 * `?tab=vacaciones&ausente=&desde=&hasta=&motivo=` abre el editor precargado
 * (CTA "Armar grilla de cobertura" de Aprobaciones). */
function TurnosAdminTabsContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const tab: Tab = searchParams.get("tab") === "vacaciones" ? "vacaciones" : "titular";

  const ausente = searchParams.get("ausente");
  const desde = searchParams.get("desde");
  const hasta = searchParams.get("hasta");
  const precargaInicial: PrecargaInicial | null =
    tab === "vacaciones" && ausente && desde && hasta
      ? { ausenteId: ausente, desde, hasta, motivo: searchParams.get("motivo") ?? "" }
      : null;

  return (
    <div className="flex flex-col gap-6">
      <SegmentedControl
        label="Sección de turnos"
        options={TABS}
        value={tab}
        onChange={(v) => router.replace(v === "titular" ? pathname : `${pathname}?tab=${v}`)}
      />
      {tab === "titular" ? (
        <CasillasManager />
      ) : (
        <ModoVacacionesView precargaInicial={precargaInicial} />
      )}
    </div>
  );
}

export function TurnosAdminTabs() {
  return (
    <Suspense
      fallback={
        <div className="flex justify-center p-8">
          <Spinner />
        </div>
      }
    >
      <TurnosAdminTabsContent />
    </Suspense>
  );
}
