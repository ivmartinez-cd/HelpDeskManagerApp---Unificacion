"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { CalendarClock, Plus } from "lucide-react";
import { ApiError } from "@/services/http-client";
import { useSession } from "@/services/session-provider";
import { BrandButton, BrandEmptyState, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { asistenciasApi } from "../api/asistencias-api";
import { formatFecha, iniciales } from "../lib/fechas";
import { TIPO_AUSENCIA, horarioTexto } from "../lib/tipos-ausencia";
import { TIPOS_SOLICITABLES, type Ausencia } from "../types/vacaciones";
import { NovedadModal } from "./novedad-modal";
import { SolicitudEstadoBadge } from "./solicitud-estado-badge";

/** Pestaña "Home office y horario" de Asistencias (hasta 2026-09-03 vivía en
 * Mis Solicitudes): las novedades propias (el backend ya acota a lo propio
 * para quien no gestiona), con su estado, y el alta. Una PENDING se puede
 * cancelar; las decididas quedan como historial. */
export function MisNovedades() {
  const { user, can } = useSession();
  const puedeCrear = user.isSuperadmin || can("vacaciones", "create") || can("vacaciones", "manage");
  const [items, setItems] = useState<Ausencia[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [creando, setCreando] = useState(false);
  const [cancelandoId, setCancelandoId] = useState<string | null>(null);

  const load = useCallback(
    () =>
      asistenciasApi
        .list()
        .then((todas) => {
          setItems(todas.filter((a) => TIPOS_SOLICITABLES.includes(a.tipo)));
          setError(null);
        })
        .catch((err: unknown) => {
          console.error("Error al cargar novedades:", err);
          setError("No se pudieron cargar las solicitudes. Intentá de nuevo.");
        }),
    [],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const ordenadas = useMemo(
    () => [...(items ?? [])].sort((a, b) => b.startDate.localeCompare(a.startDate)),
    [items],
  );

  const cancelar = (a: Ausencia) => {
    if (!window.confirm("¿Cancelar esta solicitud?")) return;
    setCancelandoId(a.id);
    asistenciasApi
      .remove(a.id)
      .then(load)
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudo cancelar la solicitud.");
      })
      .finally(() => setCancelandoId(null));
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="font-body text-sm text-muted-foreground">
          Home office y cambios de horario puntuales. Los aprueba tu TL; al aprobarse impactan en
          el calendario de asistencias y en Turnos.
        </p>
        {puedeCrear && (
          <BrandButton onClick={() => setCreando(true)}>
            <Plus className="h-4 w-4" />
            Nueva solicitud
          </BrandButton>
        )}
      </div>

      {items === null && !error && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 3 }, (_, i) => (
            <BrandSkeleton key={i} className="h-14 w-full" />
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

      {items !== null && !error && ordenadas.length === 0 && (
        <BrandEmptyState
          icon={CalendarClock}
          title="Sin solicitudes de home office ni cambios de horario"
          description="Creá una para pedir trabajo remoto o un horario distinto por unos días."
        />
      )}

      {items !== null && !error && ordenadas.length > 0 && (
        <div className="overflow-x-auto rounded-[12px] border border-border">
          <table className="w-full min-w-[720px] font-body text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30 text-left font-heading text-[11px] uppercase tracking-[.06em] text-muted-foreground">
                <th className="px-4 py-3">Empleado</th>
                <th className="px-4 py-3">Tipo</th>
                <th className="px-4 py-3">Fechas</th>
                <th className="px-4 py-3">Horario</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3">Motivo</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {ordenadas.map((a) => (
                <tr key={a.id} className="border-b border-border/60 last:border-0">
                  <td className="px-4 py-3">
                    <span className="flex items-center gap-2.5">
                      <span
                        className="flex h-7 w-7 flex-none items-center justify-center rounded-[7px] font-heading text-[10px] font-bold text-white"
                        style={{ backgroundColor: a.empleadoColor }}
                      >
                        {iniciales(a.empleadoNombre)}
                      </span>
                      <span className="font-semibold text-foreground">{a.empleadoNombre}</span>
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1.5">
                      <span
                        className="h-[7px] w-[7px] flex-none rounded-full"
                        style={{ backgroundColor: TIPO_AUSENCIA[a.tipo].color }}
                      />
                      <span className="text-foreground">{TIPO_AUSENCIA[a.tipo].label}</span>
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-foreground">
                    {a.startDate === a.endDate
                      ? formatFecha(a.startDate)
                      : `${formatFecha(a.startDate)} – ${formatFecha(a.endDate)}`}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{horarioTexto(a) ?? "—"}</td>
                  <td className="px-4 py-3">
                    <SolicitudEstadoBadge estado={a.status} />
                  </td>
                  <td className="max-w-[200px] truncate px-4 py-3 text-muted-foreground" title={a.reason ?? ""}>
                    {a.reason ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {a.status === "PENDING" && (
                      <button
                        type="button"
                        onClick={() => cancelar(a)}
                        disabled={cancelandoId === a.id}
                        className="rounded-[8px] border border-destructive/40 px-3 py-1.5 text-xs font-semibold text-destructive hover:bg-destructive/10 disabled:opacity-50"
                      >
                        Cancelar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {creando && (
        <NovedadModal
          onClose={() => setCreando(false)}
          onSaved={() => {
            setCreando(false);
            void load();
          }}
        />
      )}
    </div>
  );
}
