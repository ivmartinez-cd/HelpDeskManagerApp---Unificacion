"use client";

import { useEffect, useState } from "react";
import { ChevronRight } from "lucide-react";
import { ApiError } from "@/services/http-client";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { solicitudesApi } from "../api/solicitudes-api";
import { formatRango, iniciales } from "../lib/fechas";
import type { DecisionResult, Saldo, Solicitud } from "../types/vacaciones";
import { SolicitudEstadoBadge } from "./solicitud-estado-badge";

/** Card expandible de una solicitud de vacaciones pendiente de aprobación,
 * extraída de `aprobaciones-view.tsx` porque ese archivo ya superaba el
 * tamaño máximo de archivo (§4). */
export function AprobacionCard({
  solicitud,
  onDecided,
}: {
  solicitud: Solicitud;
  onDecided: (resultado: DecisionResult) => void;
}) {
  const [expandida, setExpandida] = useState(false);
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState<"APPROVED" | "REJECTED" | null>(null);
  const [saldo, setSaldo] = useState<Saldo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!expandida || saldo !== null) return;
    solicitudesApi
      .saldoEmpleado(solicitud.empleadoId, solicitud.chargedToYear ?? undefined)
      .then(setSaldo)
      .catch(() => setSaldo(null));
  }, [expandida, saldo, solicitud]);

  const decidir = (decision: "APPROVED" | "REJECTED") => {
    setBusy(decision);
    setError(null);
    solicitudesApi
      .decide(solicitud.id, decision, comment || null)
      .then(onDecided)
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudo registrar la decisión.");
      })
      .finally(() => setBusy(null));
  };

  return (
    <div className="rounded-[12px] border border-border bg-card">
      <button
        type="button"
        onClick={() => setExpandida((v) => !v)}
        className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
      >
        <div className="flex items-center gap-3">
          <span
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px] font-heading text-xs font-bold text-white"
            style={{ backgroundColor: solicitud.empleadoColor }}
          >
            {iniciales(solicitud.empleadoNombre)}
          </span>
          <div>
            <p className="font-body text-sm font-semibold text-foreground">
              {solicitud.empleadoNombre}
            </p>
            <p className="font-body text-xs text-muted-foreground">
              {solicitud.sectorNombre}
              {solicitud.reason ? ` · ${solicitud.reason}` : ""}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="font-body text-sm font-semibold text-foreground">
              {formatRango(solicitud.startDate, solicitud.endDate)}
            </p>
            <p className="font-body text-xs text-muted-foreground">
              {solicitud.daysRequested} días hábiles
              {saldo ? ` · Saldo: ${saldo.available} disp.` : ""}
            </p>
          </div>
          <SolicitudEstadoBadge estado={solicitud.status} />
          <ChevronRight
            className={`h-4 w-4 text-muted-foreground transition-transform ${expandida ? "rotate-90" : ""}`}
          />
        </div>
      </button>

      {expandida && (
        <div className="flex flex-col gap-3 border-t border-border px-5 py-4">
          {error && (
            <p className="rounded-[8px] border border-destructive/20 bg-destructive/10 px-3.5 py-2.5 font-body text-xs text-foreground">
              {error}
            </p>
          )}
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Comentario (opcional)…"
            rows={2}
            maxLength={500}
            className="w-full rounded-[10px] border border-border bg-background px-3.5 py-2.5 font-body text-sm text-foreground outline-none placeholder:text-muted-foreground focus:border-brand-orange"
          />
          <div className="flex justify-end gap-2">
            <BrandButton
              variant="outline"
              onClick={() => decidir("REJECTED")}
              loading={busy === "REJECTED"}
              disabled={busy !== null}
              className="border-destructive/40 text-destructive hover:bg-destructive/10"
            >
              Rechazar
            </BrandButton>
            <BrandButton
              onClick={() => decidir("APPROVED")}
              loading={busy === "APPROVED"}
              disabled={busy !== null}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              Aprobar
            </BrandButton>
          </div>
        </div>
      )}
    </div>
  );
}
