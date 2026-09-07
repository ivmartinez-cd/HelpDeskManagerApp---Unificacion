"use client";

import { useState } from "react";
import { toast } from "sonner";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { liquidacionesApi } from "../api/liquidaciones-api";
import { SpstZonaSelect } from "./spst-zona-select";

/** Bloque del modal Gestionar para una ALT008 cuya fila de Tabla KM no tiene
 * SPST: la TL elige la zona acá mismo y el backend reanaliza — reemplaza el
 * viaje a Tabla KM → buscar → editar → volver → Reanalizar. Como todos los
 * incidentes de la sucursal comparten la fila, se resuelven juntos. */
export function AsignarZonaSucursal({
  prestadorId,
  empresaNombre,
  sucursalNombre,
  incidentesAfectados,
  onAsignada,
}: {
  prestadorId: string;
  empresaNombre: string;
  sucursalNombre: string;
  /** Incidentes de esta liquidación con la misma empresa+sucursal. */
  incidentesAfectados: number;
  onAsignada: () => void;
}) {
  // "" = tarifa genérica del prestador (spstId null), igual que en el selector.
  const [seleccion, setSeleccion] = useState("");
  const [enviando, setEnviando] = useState(false);

  const asignar = async () => {
    setEnviando(true);
    try {
      await liquidacionesApi.asignarZonaSucursal({
        prestadorId,
        empresaNombre,
        sucursalNombre,
        spstId: seleccion || null,
      });
      toast.success("Zona asignada — la liquidación se reanalizó");
      onAsignada();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "No se pudo asignar la zona");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="flex flex-col gap-2 rounded-[10px] border border-brand-orange/30 bg-brand-orange/5 p-3">
      <p className="font-body text-xs text-muted-foreground">
        La sucursal <span className="font-semibold text-foreground">{sucursalNombre}</span>{" "}
        ({empresaNombre}) no tiene zona en Tabla KM, así que el motor no encuentra tarifa.
        {incidentesAfectados > 1 && (
          <> Afecta a {incidentesAfectados} incidentes de esta liquidación.</>
        )}
      </p>
      <SpstZonaSelect
        prestadorId={prestadorId}
        value={seleccion}
        onChange={setSeleccion}
        label="Zona de la sucursal"
        disabled={enviando}
      />
      <div className="flex justify-end">
        <BrandButton loading={enviando} onClick={() => void asignar()}>
          Asignar zona y reanalizar
        </BrandButton>
      </div>
    </div>
  );
}
