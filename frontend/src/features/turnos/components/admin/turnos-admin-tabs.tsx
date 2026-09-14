"use client";

import { Suspense } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { CasillasManager } from "./casillas-manager";
import { ModoVacacionesView } from "../modo-vacaciones/modo-vacaciones-view";
import type { PrecargaInicial } from "../modo-vacaciones/variante-editor";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { Spinner } from "@/shared/components/ui/spinner";
import { hoyIso } from "../../lib/variante-estado";

const TABS = [
  { value: "titular", label: "Grilla titular" },
  { value: "variantes", label: "Horarios especiales" },
];

type Tab = "titular" | "variantes";

/** /turnos: grilla titular (casillas/franjas/enroque) y horarios especiales / grillas alternativas
 * como pestañas.
 * `?tab=variantes&ajustar=hoy` abre el editor precargado para el día de hoy. */
function TurnosAdminTabsContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const rawTab = searchParams.get("tab");
  const tab: Tab = rawTab === "variantes" || rawTab === "vacaciones" ? "variantes" : "titular";

  const ausente = searchParams.get("ausente");
  const desde = searchParams.get("desde");
  const hasta = searchParams.get("hasta");
  const ajustar = searchParams.get("ajustar");

  const precargaInicial: PrecargaInicial | null =
    tab === "variantes"
      ? ajustar === "hoy"
        ? {
            ausenteId: null,
            desde: hoyIso(),
            hasta: hoyIso(),
            motivo: `Ajuste del día ${hoyIso().slice(8, 10)}/${hoyIso().slice(5, 7)}`,
          }
        : ausente && desde && hasta
          ? { ausenteId: ausente, desde, hasta, motivo: searchParams.get("motivo") ?? "" }
          : null
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
        <ModoVacacionesView key={precargaInicial ? `${precargaInicial.desde}-${precargaInicial.hasta}-${precargaInicial.ausenteId ?? "none"}` : "default"} precargaInicial={precargaInicial} />
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
