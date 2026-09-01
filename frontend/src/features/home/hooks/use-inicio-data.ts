"use client";

import { useEffect, useState } from "react";
import { accesosApi } from "@/features/home/api/accesos-api";
import { contadoresApi } from "@/features/contadores/api/contadores-api";
import type {
  AnexosSinProcesarResumen,
  CalendarEvent,
  ClientesPendientesPeriodo,
  ResumenClientesOperador,
} from "@/features/contadores/types/calendario";
import { formatDateLocal } from "@/features/contadores/utils/calendario-format";
import { prestadoresApi } from "@/features/prestadores/api/prestadores-api";
import { asistenciasApi } from "@/features/vacaciones/api/asistencias-api";
import { solicitudesApi } from "@/features/vacaciones/api/solicitudes-api";
import { hoyIso } from "@/features/vacaciones/lib/fechas";
import type { Ausencia, Solicitud } from "@/features/vacaciones/types/vacaciones";
import type { PrestadoresResumen } from "@/features/prestadores/types/prestadores";
import { pendientesApi } from "@/features/sla/api/pendientes-api";
import type { PendientesResumen } from "@/features/sla/types/pendientes";
import { slaApi } from "@/features/sla/api/sla-api";
import type { SlaResumen } from "@/features/sla/types/sla";
import { insumosApi } from "@/features/insumos/api/insumos-api";
import type { DashboardResponse } from "@/features/insumos/types/dashboard";
import { liquidacionesApi } from "@/features/liquidaciones/api/liquidaciones-api";
import { turnosApi } from "@/features/turnos/api/turnos-api";
import type { CurrentShifts } from "@/features/turnos/types/turnos";
import { periodoOffset } from "../utils/inicio-format";

export interface Remote<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

/** Refresco periódico de todo Inicio (ver `useDashboardData`): cada hook
 * recibe la misma `refreshKey`; cuando cambia, vuelve a pedir sin pasar por
 * `loading` (el dato viejo se queda en pantalla hasta que llega el nuevo). */
export function useRemote<T>(
  enabled: boolean,
  fetcher: () => Promise<T>,
  label: string,
  refreshKey = 0,
): Remote<T> {
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
  }, [enabled, tick, refreshKey]);

  return { ...state, refetch: () => setTick((t) => t + 1) };
}

export function useTurnosHoy(refreshKey = 0): Remote<CurrentShifts> {
  return useRemote(true, () => turnosApi.getCurrentShifts(), "los turnos del día", refreshKey);
}

/** Ranking personal de rutas más visitadas (30 días, backend). Si falla o
 * viene vacío (usuario nuevo, sin historial todavía), `accesos-directos.tsx`
 * completa con el respaldo fijo del catálogo — no hace falta que este hook
 * degrade a nada especial. */
export function useAccesosRanking(): Remote<string[]> {
  return useRemote(true, () => accesosApi.getTopRoutes(6), "los accesos directos");
}

export function useParqueResumen(enabled: boolean, refreshKey = 0): Remote<PrestadoresResumen> {
  return useRemote(enabled, () => prestadoresApi.getResumen(), "el parque por operador", refreshKey);
}

export function useContadoresResumen(
  enabled: boolean,
  refreshKey = 0,
): Remote<ResumenClientesOperador> {
  return useRemote(
    enabled,
    () => contadoresApi.getResumenClientesOperador(),
    "los contadores por operador",
    refreshKey,
  );
}

export function useClientesPendientesPeriodoAnterior(
  enabled: boolean,
  refreshKey = 0,
): Remote<ClientesPendientesPeriodo> {
  return useRemote(
    enabled,
    () => contadoresApi.getClientesPendientesPeriodoAnterior(),
    "el arrastre del cierre anterior",
    refreshKey,
  );
}

/** Clientes del período de facturación EN CURSO que todavía siguen en el
 * calendario de Gestión, un evento por cliente (vencidos o no) — alimenta el
 * número grande y el desglose de "Facturación sin cerrar" durante el
 * arrastre, que antes reusaba la cartera estática de 90 días (nunca bajaba)
 * y después el backlog de atraso puro (subcontaba: no incluía los que
 * todavía no llegaron a su fecha). */
export function useClientesPendientesPeriodoActual(
  enabled: boolean,
  refreshKey = 0,
): Remote<CalendarEvent[]> {
  return useRemote(
    enabled,
    () =>
      contadoresApi
        .getClientesPendientesPeriodoActual(formatDateLocal(new Date()))
        .then((page) => page.items),
    "los pendientes del período en curso",
    refreshKey,
  );
}

export interface SlaHistoria {
  /** Cronológico: [hace 5 meses, ..., mes anterior, mes actual]. Un mes sin
   * datos (o cuyo fetch falló) queda en null — solo el mes actual es fatal. */
  resumenes: (SlaResumen | null)[];
  periodos: string[];
}

const SLA_MESES = 6;

export function useSlaHistoria(enabled: boolean, refreshKey = 0): Remote<SlaHistoria> {
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
    refreshKey,
  );
}

export function usePendientesResumen(enabled: boolean, refreshKey = 0): Remote<PendientesResumen> {
  return useRemote(enabled, () => pendientesApi.getResumen(), "los pendientes a cerrar", refreshKey);
}

export function useInsumosDashboard(enabled: boolean, refreshKey = 0): Remote<DashboardResponse> {
  return useRemote(enabled, () => insumosApi.getDashboard(), "el dashboard de Insumos", refreshKey);
}

/** KPI de Inicio "Anexos sin procesar" (ver contadoresApi.getAnexosSinProcesarResumen):
 * clientes con evento vencido en el calendario cuyos anexos todavía no
 * tienen Nro_Proceso del último período ya cerrado con seguridad. Si Siges
 * no responde el endpoint devuelve 502 y este hook queda en `error` — el
 * tile debe mostrar "—", nunca un 0 inventado. */
export function useAnexosSinProcesar(
  enabled: boolean,
  refreshKey = 0,
): Remote<AnexosSinProcesarResumen> {
  return useRemote(
    enabled,
    () => contadoresApi.getAnexosSinProcesarResumen(formatDateLocal(new Date())),
    "los anexos sin procesar",
    refreshKey,
  );
}

export interface LiquidacionesPendientes {
  pendientes: number;
  porPrestador: { nombreCorto: string; count: number }[];
}

export function useLiquidacionesPendientes(
  enabled: boolean,
  refreshKey = 0,
): Remote<LiquidacionesPendientes> {
  return useRemote(
    enabled,
    () => liquidacionesApi.getResumen(),
    "el resumen de liquidaciones",
    refreshKey,
  );
}

const PROXIMOS_EQUIPO_DIAS = 21;

function addDiasIso(iso: string, n: number): string {
  const [y, m, d] = iso.split("-").map(Number);
  return formatDateLocal(new Date(y, m - 1, d + n));
}

export interface ProximosEquipo {
  vacaciones: Solicitud[];
  homeOffice: Ausencia[];
}

/** Próximos 21 días: vacaciones aprobadas y home office agendado, para la
 * card "Próximos días del equipo" de Inicio. Reusa /solicitudes y /ausencias
 * filtrando por start_date en rango (mismo semántica en ambos repos). */
export function useProximosEquipo(enabled: boolean, refreshKey = 0): Remote<ProximosEquipo> {
  return useRemote(
    enabled,
    async () => {
      const desde = hoyIso();
      const hasta = addDiasIso(desde, PROXIMOS_EQUIPO_DIAS);
      const [vacaciones, homeOffice] = await Promise.all([
        solicitudesApi.list({ status: "APPROVED", desde, hasta }),
        asistenciasApi.list({ tipo: "HOME_OFFICE", desde, hasta }),
      ]);
      return { vacaciones, homeOffice };
    },
    "los próximos días del equipo",
    refreshKey,
  );
}
