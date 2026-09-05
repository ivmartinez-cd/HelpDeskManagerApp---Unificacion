"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { Spst } from "../types/liquidaciones";

// Sentinel del select: zona Genérica (tarifario sin SPST).
const GENERICA = "__generica__";

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
  const [spsts, setSpsts] = useState<Spst[] | null>(null);
  const [seleccion, setSeleccion] = useState(GENERICA);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    liquidacionesApi
      .listSpsts({ prestadorId, soloActivos: true })
      .then(setSpsts)
      .catch(() => setSpsts([]));
  }, [prestadorId]);

  const asignar = async () => {
    setEnviando(true);
    try {
      await liquidacionesApi.asignarZonaSucursal({
        prestadorId,
        empresaNombre,
        sucursalNombre,
        spstId: seleccion === GENERICA ? null : seleccion,
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
      <label className="flex flex-col gap-1 font-body text-xs text-muted-foreground">
        Zona de la sucursal
        <select
          value={seleccion}
          onChange={(e) => setSeleccion(e.target.value)}
          disabled={spsts === null || enviando}
          className="rounded-[8px] border border-border bg-background px-3 py-2 font-body text-sm text-foreground outline-none focus:border-brand-orange"
        >
          <option value={GENERICA}>Genérica (tarifa base del prestador)</option>
          {(spsts ?? []).map((s) => (
            <option key={s.id} value={s.id}>
              {s.nombre}
              {s.zonaCobertura ? ` — ${s.zonaCobertura}` : ""}
            </option>
          ))}
        </select>
      </label>
      <div className="flex justify-end">
        <BrandButton loading={enviando} disabled={spsts === null} onClick={() => void asignar()}>
          Asignar zona y reanalizar
        </BrandButton>
      </div>
    </div>
  );
}
