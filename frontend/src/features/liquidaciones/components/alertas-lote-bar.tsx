"use client";

import { useState } from "react";
import { toast } from "sonner";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { liquidacionesApi } from "../api/liquidaciones-api";
import { useSeleccionAlertas } from "../hooks/seleccion-alertas-context";
import type { EstadoAlerta } from "../types/liquidaciones";

type Accion = {
  estado: EstadoAlerta;
  label: string;
  /** Participio para el toast, singular y plural ("1 alerta resuelta"). */
  hecho: [string, string];
  pideJustificacion?: boolean;
};

/** Mismas transiciones que `TRANSICIONES_ALERTA` desde "pendiente", que es el
 * punto de partida común de un lote (una en revisión también acepta las tres). */
const ACCIONES: Accion[] = [
  { estado: "en_revision", label: "Revisar", hecho: ["en revisión", "en revisión"] },
  { estado: "resuelta", label: "Resolver", hecho: ["resuelta", "resueltas"] },
  {
    estado: "descartada",
    label: "Descartar",
    hecho: ["descartada", "descartadas"],
    pideJustificacion: true,
  },
];

function plural(n: number, uno: string, varios: string) {
  return `${n} ${n === 1 ? uno : varios}`;
}

/** Barra flotante que aparece al tildar incidentes en el detalle: aplica el
 * mismo estado y motivo a todas sus alertas abiertas en una sola llamada
 * (`PATCH .../alertas/estado`). */
export function AlertasLoteBar({
  liquidacionId,
  onChanged,
}: {
  liquidacionId: string;
  onChanged: () => void;
}) {
  const seleccion = useSeleccionAlertas();
  const [accion, setAccion] = useState<Accion | null>(null);
  const [justificacion, setJustificacion] = useState("");
  const [enviando, setEnviando] = useState(false);

  if (!seleccion || seleccion.alertasSeleccionadas.length === 0) return null;
  const { seleccionados, alertasSeleccionadas, limpiar } = seleccion;
  const nAlertas = alertasSeleccionadas.length;

  const confirmar = async () => {
    if (!accion) return;
    setEnviando(true);
    try {
      const { actualizadas } = await liquidacionesApi.updateEstadoAlertasLote(liquidacionId, {
        alertaIds: alertasSeleccionadas.map((a) => a.id),
        estado: accion.estado,
        ...(justificacion.trim() ? { justificacion: justificacion.trim() } : {}),
      });
      toast.success(
        `${plural(actualizadas, "alerta", "alertas")} ${accion.hecho[actualizadas === 1 ? 0 : 1]}`,
      );
      setAccion(null);
      setJustificacion("");
      limpiar();
      onChanged();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "No se pudieron actualizar las alertas");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <>
      <div
        role="toolbar"
        aria-label="Alertas seleccionadas"
        className="fixed bottom-6 left-1/2 z-40 flex -translate-x-1/2 flex-wrap items-center gap-3 rounded-[12px] border border-brand-orange/40 bg-card px-5 py-3 shadow-lg"
      >
        <span className="font-body text-sm font-semibold text-foreground">
          {plural(seleccionados.size, "incidente", "incidentes")} ·{" "}
          {plural(nAlertas, "alerta seleccionada", "alertas seleccionadas")}
        </span>
        {ACCIONES.map((a) => (
          <BrandButton key={a.estado} size="sm" onClick={() => setAccion(a)}>
            {a.label}
          </BrandButton>
        ))}
        <BrandButton size="sm" variant="outline" onClick={limpiar}>
          Limpiar
        </BrandButton>
      </div>

      {accion && (
        <BrandModal
          isOpen
          onClose={() => setAccion(null)}
          title={`${accion.label} ${plural(nAlertas, "alerta", "alertas")}`}
          widthPx={460}
        >
          <div className="flex flex-col gap-4">
            <p className="font-body text-sm text-muted-foreground">
              El mismo motivo se guarda en las {nAlertas} alertas de los{" "}
              {seleccionados.size} incidentes tildados.
            </p>
            <textarea
              value={justificacion}
              onChange={(e) => setJustificacion(e.target.value)}
              rows={3}
              placeholder={
                accion.pideJustificacion
                  ? "Ej.: costo doble acordado con el prestador para toda la zona"
                  : "Nota (opcional)"
              }
              autoFocus
              className="w-full rounded-[8px] border border-border bg-background p-3 font-body text-sm text-foreground outline-none focus:border-brand-orange"
            />
            <div className="flex justify-end gap-2">
              <BrandButton variant="outline" onClick={() => setAccion(null)}>
                Volver
              </BrandButton>
              <BrandButton
                loading={enviando}
                disabled={accion.pideJustificacion && !justificacion.trim()}
                onClick={() => void confirmar()}
              >
                {accion.label} {plural(nAlertas, "alerta", "alertas")}
              </BrandButton>
            </div>
          </div>
        </BrandModal>
      )}
    </>
  );
}
