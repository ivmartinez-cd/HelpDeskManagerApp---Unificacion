"use client";

import { useState } from "react";
import { toast } from "sonner";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { Alerta, Incidente } from "../types/liquidaciones";

const JUSTIFICACION_RUTA = "Km asociado a otro incidente";

interface Candidato {
  incidente_id: string;
  numero_incidente: string;
  empresa: string | null;
  sucursal: string | null;
  km: number | null;
}

interface CtxKm {
  cobrado?: number;
  sin_referencia?: boolean;
  posible_ruta_compartida?: boolean;
  candidatos?: Candidato[];
}

/** Acciones de un clic para las dos ALT002 que la TL resolvía siempre igual:
 * la fila de Tabla KM sin km ("tomar lo cobrado como referencia") y el
 * "cobró 0 km porque fue en el mismo viaje" (ruta compartida con el incidente
 * del mismo día que sí cobró km). En las liquidaciones abiertas al 2026-09-05
 * eran 40 de las 45 alertas de km pendientes. */
export function AlertaKmAcciones({
  liquidacionId,
  prestadorId,
  alerta,
  incidente,
  onChanged,
  onClose,
}: {
  liquidacionId: string;
  prestadorId: string;
  alerta: Alerta;
  incidente: Incidente;
  onChanged: () => void;
  onClose: () => void;
}) {
  const ctx = (alerta.datosContexto ?? {}) as CtxKm;
  const candidatos = ctx.candidatos ?? [];
  const [candidatoId, setCandidatoId] = useState(candidatos[0]?.incidente_id ?? "");
  const [enviando, setEnviando] = useState(false);

  const correr = async (fn: () => Promise<unknown>, okMsg: string) => {
    setEnviando(true);
    try {
      await fn();
      toast.success(okMsg);
      onChanged();
      onClose();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "No se pudo aplicar");
    } finally {
      setEnviando(false);
    }
  };

  if (ctx.sin_referencia && incidente.empresaNombre && incidente.sucursalNombre) {
    const cobrado = ctx.cobrado ?? 0;
    return (
      <div className="flex flex-col gap-2 rounded-[10px] border border-brand-orange/30 bg-brand-orange/5 p-3">
        <p className="font-body text-xs text-muted-foreground">
          La sucursal <span className="font-semibold text-foreground">{incidente.sucursalNombre}</span> no
          tiene km de referencia en Tabla KM. Si los {cobrado} km cobrados son los correctos, quedan
          como referencia para todas las liquidaciones que vengan.
        </p>
        <div className="flex justify-end">
          <BrandButton
            loading={enviando}
            onClick={() =>
              void correr(
                () =>
                  liquidacionesApi.fijarKmReferencia({
                    prestadorId,
                    empresaNombre: incidente.empresaNombre!,
                    sucursalNombre: incidente.sucursalNombre!,
                    kms: cobrado,
                  }),
                `${cobrado} km quedaron como referencia — la liquidación se reanalizó`,
              )
            }
          >
            Tomar {cobrado} km como referencia
          </BrandButton>
        </div>
      </div>
    );
  }

  if (ctx.posible_ruta_compartida && candidatos.length > 0) {
    const elegido = candidatos.find((c) => c.incidente_id === candidatoId);
    return (
      <div className="flex flex-col gap-2 rounded-[10px] border border-brand-orange/30 bg-brand-orange/5 p-3">
        <p className="font-body text-xs text-muted-foreground">
          Cobró 0 km. El mismo día el prestador sí cobró km en otro incidente: probablemente fue el
          mismo viaje.
        </p>
        <label className="flex flex-col gap-1 font-body text-xs text-muted-foreground">
          Mismo viaje que
          <select
            value={candidatoId}
            onChange={(e) => setCandidatoId(e.target.value)}
            disabled={enviando}
            className="rounded-[8px] border border-border bg-background px-3 py-2 font-body text-sm text-foreground outline-none focus:border-brand-orange"
          >
            {candidatos.map((c) => (
              <option key={c.incidente_id} value={c.incidente_id}>
                #{c.numero_incidente} — {[c.empresa, c.sucursal].filter(Boolean).join(" / ")} ({c.km} km)
              </option>
            ))}
          </select>
        </label>
        <div className="flex justify-end">
          <BrandButton
            loading={enviando}
            disabled={!elegido}
            onClick={() =>
              void correr(
                () =>
                  liquidacionesApi.updateEstadoAlerta(liquidacionId, alerta.id, {
                    estado: "resuelta",
                    justificacion: JUSTIFICACION_RUTA,
                    incidenteRelacionadoId: candidatoId,
                  }),
                `Ruta compartida con #${elegido?.numero_incidente} confirmada`,
              )
            }
          >
            Confirmar ruta compartida
          </BrandButton>
        </div>
      </div>
    );
  }

  return null;
}
