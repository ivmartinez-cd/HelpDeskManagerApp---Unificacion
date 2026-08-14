"use client";

import { useEffect, useState } from "react";
import { contadoresApi } from "@/features/contadores/api/contadores-api";
import type {
  CalendarEvent,
  Operador,
  ResumenClientesOperador,
} from "@/features/contadores/types/calendario";
import { formatDateLocal } from "@/features/contadores/utils/calendario-format";
import { prestadoresApi } from "@/features/prestadores/api/prestadores-api";
import type { PrestadoresResumen } from "@/features/prestadores/types/prestadores";
import { slaApi } from "@/features/sla/api/sla-api";
import type { SlaResumen } from "@/features/sla/types/sla";
import { turnosApi } from "@/features/turnos/api/turnos-api";
import type { ResolvedShift } from "@/features/turnos/types/turnos";
import { periodoOffset } from "../utils/inicio-format";

export interface Remote<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

function useRemote<T>(enabled: boolean, fetcher: () => Promise<T>, label: string): Remote<T> {
  const [tick, setTick] = useState(0);
  const [state, setState] = useState<Omit<Remote<T>, "refetch">>({
    data: null,
    loading: enabled,
    error: null,
  });

  useEffect(() => {
    if (!enabled) return;
    let alive = true;
    fetcher()
      .then((data) => alive && setState({ data, loading: false, error: null }))
      .catch((err: unknown) => {
        console.error(`Error al cargar ${label}:`, err);
        if (alive) {
          setState({
            data: null,
            loading: false,
            error: err instanceof Error ? err.message : `No se pudo cargar ${label}.`,
          });
        }
      });
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, tick]);

  return { ...state, refetch: () => setTick((t) => t + 1) };
}

export function useTurnosHoy(): Remote<ResolvedShift[]> {
  return useRemote(true, () => turnosApi.getCurrentShifts(), "los turnos del día");
}

export function useParqueResumen(enabled: boolean): Remote<PrestadoresResumen> {
  return useRemote(enabled, () => prestadoresApi.getResumen(), "el parque por operador");
}

export function useContadoresResumen(enabled: boolean): Remote<ResumenClientesOperador> {
  return useRemote(
    enabled,
    () => contadoresApi.getResumenClientesOperador(),
    "los contadores por operador",
  );
}

export interface SlaHistoria {
  /** Cronológico: [hace 5 meses, ..., mes anterior, mes actual]. Un mes sin
   * datos (o cuyo fetch falló) queda en null — solo el mes actual es fatal. */
  resumenes: (SlaResumen | null)[];
  periodos: string[];
}

const SLA_MESES = 6;

export function useSlaHistoria(enabled: boolean): Remote<SlaHistoria> {
  const periodos = Array.from({ length: SLA_MESES }, (_, i) => periodoOffset(i - SLA_MESES + 1));
  return useRemote(
    enabled,
    async () => {
      const resumenes = await Promise.all(
        periodos.map((p, i) =>
          slaApi.getResumen(p).catch((err: unknown) => {
            // El mes actual sí corta la card; la historia previa degrada a null.
            if (i === SLA_MESES - 1) throw err;
            console.error(`Error al cargar el resumen SLA de ${p}:`, err);
            return null;
          }),
        ),
      );
      return { resumenes, periodos };
    },
    "el resumen SLA",
  );
}

export interface CalendarioHome {
  hoy: CalendarEvent[];
  subtituloHoy: string;
  pendientes: CalendarEvent[];
  semana: CalendarEvent[];
  operadores: Operador[];
  lastSyncedAt: string | null;
}

/** Rango de "Clientes de hoy": viernes muestra viernes+sábado y lunes
 * muestra domingo+lunes (mismo criterio que la card anterior de Inicio). */
function rangoHoy(now: Date): { start: string; end: string; subtitulo: string } {
  const day = now.getDay();
  const shift = (d: number) => formatDateLocal(new Date(now.getFullYear(), now.getMonth(), now.getDate() + d));
  if (day === 5) return { start: shift(0), end: shift(1), subtitulo: "Viernes y sábado" };
  if (day === 1) return { start: shift(-1), end: shift(0), subtitulo: "Domingo y lunes" };
  return { start: shift(0), end: shift(0), subtitulo: "Planificación de Contadores" };
}

/** Lunes a sábado de la semana en curso, para el heatmap. */
function rangoSemana(now: Date): { start: string; end: string } {
  const lunes = new Date(now.getFullYear(), now.getMonth(), now.getDate() - ((now.getDay() + 6) % 7));
  const sabado = new Date(lunes.getFullYear(), lunes.getMonth(), lunes.getDate() + 5);
  return { start: formatDateLocal(lunes), end: formatDateLocal(sabado) };
}

export function useCalendarioHome(enabled: boolean): Remote<CalendarioHome> {
  return useRemote(
    enabled,
    async () => {
      const now = new Date();
      const hoy = formatDateLocal(now);
      const rango = rangoHoy(now);
      const semana = rangoSemana(now);
      const [hoyPage, pendPage, semanaPage, operadores, sync] = await Promise.all([
        contadoresApi.getCalendarioEvents({ start: rango.start, end: rango.end }),
        contadoresApi.getCalendarioPendientes(hoy),
        contadoresApi.getCalendarioEvents({ start: semana.start, end: semana.end }),
        contadoresApi.listCalendarioOperadores(),
        contadoresApi.getSyncStatus().catch((err: unknown) => {
          console.error("Error al consultar el estado de sync:", err);
          return null;
        }),
      ]);
      return {
        hoy: hoyPage.items,
        subtituloHoy: rango.subtitulo,
        pendientes: pendPage.items,
        semana: semanaPage.items,
        operadores,
        lastSyncedAt: sync?.last_synced_at ?? null,
      };
    },
    "la planificación de Contadores",
  );
}
