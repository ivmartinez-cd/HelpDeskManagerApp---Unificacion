"use client";

import { useCallback, useEffect, useState } from "react";
import { ChevronRight, ClipboardCheck } from "lucide-react";
import { ApiError } from "@/services/http-client";
import { BrandButton, BrandEmptyState, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { asistenciasApi } from "../api/asistencias-api";
import { formatRango, iniciales } from "../lib/fechas";
import { TIPO_AUSENCIA, horarioTexto } from "../lib/tipos-ausencia";
import type { AfectaTurnos, Ausencia } from "../types/vacaciones";
import { SolicitudEstadoBadge } from "./solicitud-estado-badge";

/** Aviso de impacto en turnos genérico (vacaciones o novedad aprobada). */
export interface AvisoTurnos {
  empleadoNombre: string;
  startDate: string;
  endDate: string;
  afectaTurnos: AfectaTurnos;
  /** Texto del motivo para la grilla de cobertura precargada. */
  motivo: string;
}

/** Novedades (home office, cambio de horario…) PENDING que la TL tiene que
 * decidir: mismo patrón de card expandible que las vacaciones, contra
 * /api/vacaciones/ausencias/{id}/decision. */
export function NovedadesPendientes({
  onDecided,
}: {
  onDecided: (aviso: AvisoTurnos | null) => void;
}) {
  const [items, setItems] = useState<Ausencia[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    () =>
      asistenciasApi
        .list({ status: "PENDING" })
        .then((pendientes) => {
          setItems(pendientes);
          setError(null);
        })
        .catch((err: unknown) => {
          console.error("Error al cargar novedades pendientes:", err);
          setError("No se pudieron cargar las novedades pendientes.");
        }),
    [],
  );

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <section className="flex flex-col gap-3">
      <h2 className="font-heading text-sm font-bold uppercase tracking-[.05em] text-foreground">
        Home office y cambios de horario pendientes{" "}
        {items && (
          <span className="ml-1 rounded-[20px] bg-amber-500/15 px-2 py-0.5 font-body text-xs text-amber-600 dark:text-amber-400">
            {items.length}
          </span>
        )}
      </h2>
      {items === null && !error && <BrandSkeleton className="h-16 w-full" />}
      {error && (
        <div className="flex items-center justify-between gap-4 rounded-[12px] border border-destructive/20 bg-destructive/10 px-5 py-4">
          <p className="font-body text-sm text-foreground">{error}</p>
          <BrandButton variant="outline" size="sm" onClick={() => void load()}>
            Reintentar
          </BrandButton>
        </div>
      )}
      {items !== null && !error && items.length === 0 && (
        <BrandEmptyState
          icon={ClipboardCheck}
          title="No hay novedades pendientes"
          description="Cuando alguien pida home office o un cambio de horario vas a verlo acá."
        />
      )}
      {items !== null &&
        !error &&
        items.map((a) => (
          <NovedadCard
            key={a.id}
            ausencia={a}
            onDecided={(aviso) => {
              onDecided(aviso);
              void load();
            }}
          />
        ))}
    </section>
  );
}

function NovedadCard({
  ausencia,
  onDecided,
}: {
  ausencia: Ausencia;
  onDecided: (aviso: AvisoTurnos | null) => void;
}) {
  const [expandida, setExpandida] = useState(false);
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState<"APPROVED" | "REJECTED" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const horario = horarioTexto(ausencia);

  const decidir = (decision: "APPROVED" | "REJECTED") => {
    setBusy(decision);
    setError(null);
    asistenciasApi
      .decide(ausencia.id, decision, comment || null)
      .then((res) =>
        onDecided(
          res.afectaTurnos
            ? {
                empleadoNombre: ausencia.empleadoNombre,
                startDate: ausencia.startDate,
                endDate: ausencia.endDate,
                afectaTurnos: res.afectaTurnos,
                motivo: `${TIPO_AUSENCIA[ausencia.tipo].label} ${ausencia.empleadoNombre}${horario ? ` ${horario}` : ""}`,
              }
            : null,
        ),
      )
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
            style={{ backgroundColor: ausencia.empleadoColor }}
          >
            {iniciales(ausencia.empleadoNombre)}
          </span>
          <div>
            <p className="font-body text-sm font-semibold text-foreground">
              {ausencia.empleadoNombre}
            </p>
            <p className="font-body text-xs text-muted-foreground">
              {TIPO_AUSENCIA[ausencia.tipo].label}
              {horario ? ` · ${horario}` : ""}
              {ausencia.reason ? ` · ${ausencia.reason}` : ""}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <p className="font-body text-sm font-semibold text-foreground">
            {formatRango(ausencia.startDate, ausencia.endDate)}
          </p>
          <SolicitudEstadoBadge estado={ausencia.status} />
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
