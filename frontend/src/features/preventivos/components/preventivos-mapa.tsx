"use client";

import dynamic from "next/dynamic";
import type { PuntoMapaPreventivo } from "../types/preventivos";
import { BrandSkeleton } from "@/shared/components/ui/brand-form";

// Leaflet toca `window` al montarse: sin esto el build de producción
// (next build && next start, sin --reload — ver CLAUDE.md) rompe en SSR.
const PreventivosMapaCanvas = dynamic(
  () => import("./preventivos-mapa-canvas").then((m) => m.PreventivosMapaCanvas),
  { ssr: false, loading: () => <BrandSkeleton className="h-[520px] w-full rounded-[12px]" /> },
);

interface PreventivosMapaProps {
  puntos: PuntoMapaPreventivo[];
  canUpdate: boolean;
  onEditarUbicacion: (idSucursal: number) => void;
  onCargarPreventivo: (idSucursal: number) => void;
}

export function PreventivosMapa({
  puntos,
  canUpdate,
  onEditarUbicacion,
  onCargarPreventivo,
}: PreventivosMapaProps) {
  return (
    <PreventivosMapaCanvas
      puntos={puntos}
      canUpdate={canUpdate}
      onEditarUbicacion={onEditarUbicacion}
      onCargarPreventivo={onCargarPreventivo}
    />
  );
}
