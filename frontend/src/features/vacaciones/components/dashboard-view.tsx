"use client";

import { useCallback, useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, UserX } from "lucide-react";
import { BrandButton, BrandSkeleton, BrandStatTile } from "@/shared/components/ui/brand-form";
import { solicitudesApi } from "../api/solicitudes-api";
import { labelMes, rangoDeGrilla } from "../lib/calendario";
import { formatRango, hoyIso, iniciales } from "../lib/fechas";
import type { DashboardResumen, EventoCalendario } from "../types/vacaciones";
import { VacacionesMonthGrid } from "./vacaciones-month-grid";

export function DashboardView() {
  const hoy = hoyIso();
  const [year, setYear] = useState(Number(hoy.slice(0, 4)));
  const [month, setMonth] = useState(Number(hoy.slice(5, 7)));
  const [resumen, setResumen] = useState<DashboardResumen | null>(null);
  const [eventos, setEventos] = useState<EventoCalendario[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    const { desde, hasta } = rangoDeGrilla(year, month);
    return Promise.all([solicitudesApi.dashboard(), solicitudesApi.calendario(desde, hasta)])
      .then(([res, evs]) => {
        setResumen(res);
        setEventos(evs);
        setError(null);
      })
      .catch((err: unknown) => {
        console.error("Error al cargar el dashboard:", err);
        setError("No se pudo cargar el dashboard. Intentá de nuevo.");
      });
  }, [year, month]);

  useEffect(() => {
    void load();
  }, [load]);

  const mover = (delta: number) => {
    const total = year * 12 + (month - 1) + delta;
    setYear(Math.floor(total / 12));
    setMonth((total % 12) + 1);
  };

  const dias = resumen?.dias?.saldo ?? null;

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-col gap-1.5">
        <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
          Dashboard
        </h1>
        <p className="font-body text-sm text-muted-foreground">
          Resumen general de vacaciones del equipo
        </p>
      </div>

      {error && (
        <div className="flex items-center justify-between gap-4 rounded-[12px] border border-destructive/20 bg-destructive/10 px-5 py-4">
          <p className="font-body text-sm text-foreground">{error}</p>
          <BrandButton variant="outline" size="sm" onClick={() => void load()}>
            Reintentar
          </BrandButton>
        </div>
      )}

      {resumen === null && !error && (
        <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
          {Array.from({ length: 4 }, (_, i) => (
            <BrandSkeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      )}

      {resumen !== null && !error && (
        <>
          <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
            <BrandStatTile
              label="Total empleados"
              value={String(resumen.totalEmpleados)}
              hint={`${resumen.empleadosActivos} activos`}
            />
            <BrandStatTile
              label="De vacaciones hoy"
              value={String(resumen.enVacaciones.length)}
              hint={
                resumen.enVacaciones.length > 0
                  ? resumen.enVacaciones.map((e) => e.sectorNombre).join(" · ")
                  : "Nadie ausente"
              }
            />
            <BrandStatTile
              label="Solicitudes pendientes"
              value={String(resumen.solicitudesPendientes)}
              hint="Requieren aprobación"
              tone={resumen.solicitudesPendientes > 0 ? "highlight" : "neutral"}
            />
            <BrandStatTile
              label="Días disponibles"
              value={String(
                dias?.available ?? resumen.diasDisponiblesEquipo ?? 0,
              )}
              hint={
                dias
                  ? `de ${dias.annual + dias.carryOver} totales del ciclo`
                  : resumen.diasTotalesEquipo !== null
                    ? `de ${resumen.diasTotalesEquipo} totales del equipo`
                    : "Sin empleado vinculado"
              }
            />
          </div>

          <div className="grid grid-cols-1 gap-5 xl:grid-cols-[2fr_1fr]">
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    aria-label="Mes anterior"
                    onClick={() => mover(-1)}
                    className="flex h-8 w-8 items-center justify-center rounded-[8px] border border-border text-foreground hover:bg-muted"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    aria-label="Mes siguiente"
                    onClick={() => mover(1)}
                    className="flex h-8 w-8 items-center justify-center rounded-[8px] border border-border text-foreground hover:bg-muted"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setYear(Number(hoy.slice(0, 4)));
                      setMonth(Number(hoy.slice(5, 7)));
                    }}
                    className="ml-1 rounded-[8px] border border-border px-3 py-1.5 font-body text-xs font-semibold text-foreground hover:bg-muted"
                  >
                    Hoy
                  </button>
                </div>
                <h2 className="font-heading text-base font-bold capitalize text-foreground">
                  {labelMes(year, month)}
                </h2>
                <span className="font-body text-xs text-muted-foreground">
                  Pendientes en transparencia
                </span>
              </div>
              <VacacionesMonthGrid
                year={year}
                month={month}
                hoyIso={hoy}
                eventos={eventos}
              />
            </div>

            <div className="flex flex-col gap-3 rounded-[12px] border border-border bg-card p-5">
              <h2 className="font-heading text-sm font-bold text-foreground">
                De vacaciones ahora
              </h2>
              {resumen.enVacaciones.length === 0 ? (
                <div className="flex flex-1 flex-col items-center justify-center gap-2 py-8 text-center">
                  <UserX className="h-8 w-8 text-muted-foreground/50" />
                  <p className="font-body text-sm text-muted-foreground">
                    Nadie está de vacaciones hoy
                  </p>
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  {resumen.enVacaciones.map((e) => (
                    <div
                      key={e.solicitudId}
                      className="flex items-center gap-3 rounded-[10px] bg-muted/30 px-3.5 py-3"
                    >
                      <span
                        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px] font-heading text-xs font-bold text-white"
                        style={{ backgroundColor: e.empleadoColor }}
                      >
                        {iniciales(e.empleadoNombre)}
                      </span>
                      <div className="min-w-0">
                        <p className="truncate font-body text-sm font-semibold text-foreground">
                          {e.empleadoNombre}
                        </p>
                        <p className="font-body text-xs text-muted-foreground">
                          {formatRango(e.startDate, e.endDate)} ·{" "}
                          <span style={{ color: e.sectorColor }}>{e.sectorNombre}</span>
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
