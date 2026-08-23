"use client";

import { SearchX } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import type { usePuntosMapa } from "../hooks/use-puntos-mapa";
import type { PuntoMapaPreventivo } from "../types/preventivos";
import { CorregirCoordenadaModal } from "./corregir-coordenada-modal";
import { numberFormat } from "./preventivos-format";
import { PreventivosMapa } from "./preventivos-mapa";
import { PreventivosMapaLeyenda } from "./preventivos-mapa-leyenda";
import { BrandButton, BrandEmptyState, BrandSkeleton } from "@/shared/components/ui/brand-form";

interface PreventivosMapaSeccionProps {
  mapa: ReturnType<typeof usePuntosMapa>;
  canUpdate: boolean;
}

/** Vista "mapa" de `preventivos-view.tsx` (extraído para no pasar el límite
 * de §4 del archivo padre) — dueño de su propio estado de edición: el modal
 * de corrección de coordenada vive acá, no en la vista general. */
export function PreventivosMapaSeccion({ mapa, canUpdate }: PreventivosMapaSeccionProps) {
  const [puntoEditando, setPuntoEditando] = useState<PuntoMapaPreventivo | null>(null);

  return (
    <>
      {mapa.error && (
        <div className="flex items-center justify-between gap-4 rounded-[12px] border border-destructive/20 bg-destructive/10 px-5 py-4">
          <p className="font-body text-sm text-foreground">{mapa.error}</p>
        </div>
      )}
      {!mapa.error && mapa.puntos === null && (
        <BrandSkeleton className="h-[520px] w-full rounded-[12px]" />
      )}
      {!mapa.error && mapa.puntos !== null && (
        <>
          {mapa.puntos.length === 0 ? (
            <BrandEmptyState
              icon={SearchX}
              title="Sin resultados"
              description="Ningún equipo de la zona cumple el filtro actual. Probá cambiar el estado o limpiar la búsqueda."
            />
          ) : (
            <>
              {mapa.sinUbicar > 0 && (
                <div className="flex flex-wrap items-center justify-between gap-3 rounded-[8px] bg-muted/30 px-4 py-3">
                  <p className="font-body text-xs text-muted-foreground">
                    {numberFormat.format(mapa.sinUbicar)} sucursal(es) del filtro actual no
                    tienen una coordenada válida en Siges y no se muestran en el mapa.
                  </p>
                  {canUpdate && (
                    <BrandButton
                      variant="outline"
                      size="sm"
                      loading={mapa.geocodificando}
                      onClick={mapa.geocodificar}
                      title="Geocodifica el universo completo de sucursales sin ubicar, no solo la zona actual"
                    >
                      Geocodificar sucursales sin ubicar
                    </BrandButton>
                  )}
                </div>
              )}
              <PreventivosMapa
                puntos={mapa.puntos}
                canUpdate={canUpdate}
                onEditarUbicacion={(idSucursal) =>
                  setPuntoEditando(mapa.puntos?.find((p) => p.id_sucursal === idSucursal) ?? null)
                }
              />
              <PreventivosMapaLeyenda />
            </>
          )}
        </>
      )}

      {puntoEditando && (
        <CorregirCoordenadaModal
          punto={puntoEditando}
          onClose={() => setPuntoEditando(null)}
          onSaved={() => {
            setPuntoEditando(null);
            toast.success("Coordenada corregida");
            mapa.refrescar();
          }}
        />
      )}
    </>
  );
}
