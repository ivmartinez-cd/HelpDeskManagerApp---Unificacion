"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { CalendarClock, ChevronRight, ClipboardCheck, X } from "lucide-react";
import { ApiError } from "@/services/http-client";
import {
  BrandButton,
  BrandEmptyState,
  BrandSelect,
  BrandSkeleton,
  brandButtonClasses,
} from "@/shared/components/ui/brand-form";
import { solicitudesApi } from "../api/solicitudes-api";
import { formatFecha, formatRango, iniciales } from "../lib/fechas";
import type { DecisionResult, Saldo, Solicitud } from "../types/vacaciones";
import { NovedadesPendientes, type AvisoTurnos } from "./novedades-aprobacion";
import { SolicitudEstadoBadge } from "./solicitud-estado-badge";

/** Link al editor del modo vacaciones de turnos (ADR-025), precargado por
 * query params con el ausente y el rango aprobado. */
/** Vacaciones aprobadas con impacto en turnos → aviso genérico (también lo
 * producen las novedades: home office / cambio de horario). */
function avisoDeVacaciones(decision: DecisionResult): AvisoTurnos | null {
  if (!decision.afectaTurnos) return null;
  return {
    empleadoNombre: decision.empleadoNombre,
    startDate: decision.startDate,
    endDate: decision.endDate,
    afectaTurnos: decision.afectaTurnos,
    motivo: `Vacaciones ${decision.empleadoNombre}`,
  };
}

export function hrefArmarGrillaCobertura(decision: AvisoTurnos): string {
  const q = new URLSearchParams({
    tab: "vacaciones",
    ausente: decision.afectaTurnos.userId,
    desde: decision.startDate,
    hasta: decision.endDate,
    motivo: decision.motivo,
  });
  return `/turnos?${q.toString()}`;
}

function AvisoAfectaTurnos({
  decision,
  onClose,
}: {
  decision: AvisoTurnos;
  onClose: () => void;
}) {
  return (
    <div
      role="status"
      className="flex flex-wrap items-center justify-between gap-4 rounded-[12px] border border-brand-orange/20 bg-brand-orange/10 px-5 py-4"
    >
      <div className="flex items-start gap-3">
        <CalendarClock className="mt-0.5 h-5 w-5 shrink-0 text-brand-orange" />
        <div className="flex flex-col gap-0.5">
          <p className="font-body text-sm font-semibold text-foreground">
            {decision.empleadoNombre} tiene turnos de casilla entre el{" "}
            {formatFecha(decision.startDate)} y el {formatFecha(decision.endDate)}.
          </p>
          <p className="font-body text-xs text-muted-foreground">
            La aprobación quedó registrada. La grilla de cobertura no se arma sola: re-cortar
            franjas exige criterio humano. Podés armarla ahora en el Modo vacaciones de Turnos.
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Link
          href={hrefArmarGrillaCobertura(decision)}
          className={brandButtonClasses({ size: "sm" })}
        >
          Armar grilla de cobertura →
        </Link>
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar aviso de turnos"
          className="rounded-[8px] p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

export function AprobacionesView() {
  const [solicitudes, setSolicitudes] = useState<Solicitud[] | null>(null);
  const [soloPendientes, setSoloPendientes] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [avisoTurnos, setAvisoTurnos] = useState<AvisoTurnos | null>(null);

  const load = useCallback(
    () =>
      solicitudesApi
        .list()
        .then((items) => {
          setSolicitudes(items);
          setError(null);
        })
        .catch((err: unknown) => {
          console.error("Error al cargar aprobaciones:", err);
          setError("No se pudieron cargar las solicitudes. Intentá de nuevo.");
        }),
    [],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const pendientes = useMemo(
    () => (solicitudes ?? []).filter((s) => s.status === "PENDING"),
    [solicitudes],
  );
  const listadas = soloPendientes ? pendientes : (solicitudes ?? []);
  const historial = useMemo(
    () => (solicitudes ?? []).filter((s) => s.aprobaciones.length > 0),
    [solicitudes],
  );

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
            Aprobaciones
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Revisá, aprobá o rechazá las solicitudes de vacaciones, home office y cambios de
            horario
          </p>
        </div>
        <div className="min-w-[180px]">
          <BrandSelect
            label="Mostrar"
            value={soloPendientes ? "pendientes" : "todas"}
            onChange={(e) => setSoloPendientes(e.target.value === "pendientes")}
          >
            <option value="pendientes">Sólo pendientes</option>
            <option value="todas">Todas</option>
          </BrandSelect>
        </div>
      </div>

      {solicitudes === null && !error && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 3 }, (_, i) => (
            <BrandSkeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      )}

      {error && (
        <div className="flex items-center justify-between gap-4 rounded-[12px] border border-destructive/20 bg-destructive/10 px-5 py-4">
          <p className="font-body text-sm text-foreground">{error}</p>
          <BrandButton variant="outline" size="sm" onClick={() => void load()}>
            Reintentar
          </BrandButton>
        </div>
      )}

      {avisoTurnos && (
        <AvisoAfectaTurnos decision={avisoTurnos} onClose={() => setAvisoTurnos(null)} />
      )}

      <NovedadesPendientes onDecided={setAvisoTurnos} />

      {solicitudes !== null && !error && (
        <>
          <section className="flex flex-col gap-3">
            <h2 className="font-heading text-sm font-bold uppercase tracking-[.05em] text-foreground">
              Vacaciones pendientes de aprobación{" "}
              <span className="ml-1 rounded-[20px] bg-amber-500/15 px-2 py-0.5 font-body text-xs text-amber-600 dark:text-amber-400">
                {pendientes.length}
              </span>
            </h2>
            {listadas.length === 0 ? (
              <BrandEmptyState
                icon={ClipboardCheck}
                title="No hay solicitudes para mostrar"
                description="Cuando alguien pida vacaciones vas a verlas acá."
              />
            ) : (
              listadas.map((s) => (
                <AprobacionCard
                  key={s.id}
                  solicitud={s}
                  onDecided={(res) => {
                    setAvisoTurnos(avisoDeVacaciones(res));
                    void load();
                  }}
                />
              ))
            )}
          </section>

          {historial.length > 0 && (
            <section className="flex flex-col gap-3">
              <h2 className="font-heading text-sm font-bold uppercase tracking-[.05em] text-foreground">
                Historial de decisiones
              </h2>
              <div className="overflow-x-auto rounded-[12px] border border-border">
                <table className="w-full min-w-[720px] font-body text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/30 text-left font-heading text-[11px] uppercase tracking-[.06em] text-muted-foreground">
                      <th className="px-4 py-3">Empleado</th>
                      <th className="px-4 py-3">Rango</th>
                      <th className="px-4 py-3 text-right">Días</th>
                      <th className="px-4 py-3">Decisión</th>
                      <th className="px-4 py-3">Decisor</th>
                      <th className="px-4 py-3">Comentario</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historial.map((s) => {
                      const ultima = s.aprobaciones[0];
                      return (
                        <tr key={s.id} className="border-b border-border/60 last:border-0">
                          <td className="px-4 py-3 font-semibold text-foreground">
                            {s.empleadoNombre}
                          </td>
                          <td className="px-4 py-3 text-muted-foreground">
                            {formatRango(s.startDate, s.endDate)}
                          </td>
                          <td className="px-4 py-3 text-right text-foreground">
                            {s.daysRequested}
                          </td>
                          <td className="px-4 py-3">
                            <SolicitudEstadoBadge
                              estado={ultima.decision === "APPROVED" ? "APPROVED" : "REJECTED"}
                            />
                          </td>
                          <td className="px-4 py-3 text-muted-foreground">
                            {ultima.approverEmail ?? "—"}
                          </td>
                          <td className="max-w-[220px] truncate px-4 py-3 text-muted-foreground">
                            {ultima.comment ?? "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

function AprobacionCard({
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
