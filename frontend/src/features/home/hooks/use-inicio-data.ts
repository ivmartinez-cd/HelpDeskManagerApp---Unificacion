"use client";

import { useEffect, useState } from "react";
import { accesosApi } from "@/features/home/api/accesos-api";
import { contadoresApi } from "@/features/contadores/api/contadores-api";
import type {
  CalendarEvent,
  ClientesPendientesPeriodo,
  Operador,
  ResumenClientesOperador,
} from "@/features/contadores/types/calendario";
import { formatDateLocal } from "@/features/contadores/utils/calendario-format";
import { prestadoresApi } from "@/features/prestadores/api/prestadores-api";
import { asistenciasApi } from "@/features/vacaciones/api/asistencias-api";
import { gestionApi } from "@/features/vacaciones/api/gestion-api";
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

export interface CalendarioHome {
  hoy: CalendarEvent[];
  subtituloHoy: string;
  pendientes: CalendarEvent[];
  semana: CalendarEvent[];
  operadores: Operador[];
  lastSyncedAt: string | null;
}

const NOMBRES_DIA = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];

function addDias(d: Date, n: number): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);
}

function esLaborable(d: Date, feriados: Set<string>): boolean {
  const dia = d.getDay();
  return dia !== 0 && dia !== 6 && !feriados.has(formatDateLocal(d));
}

/** Primer día del rango a mostrar "hoy": arranca en `now` y retrocede
 * mientras el día anterior sea no laborable (fin de semana y/o feriado) —
 * salvo un sábado cuyo viernes fue laborable, porque ese sábado ya lo
 * mostró el look-ahead de "viernes y sábado" (ver rangoHoy). Así un feriado
 * pegado a un fin de semana (p. ej. lunes feriado) se recupera completo el
 * primer día hábil siguiente en vez de perderse. */
function inicioDeCatchUp(now: Date, feriados: Set<string>): Date {
  let inicio = now;
  let anterior = addDias(now, -1);
  while (!esLaborable(anterior, feriados)) {
    if (anterior.getDay() === 6 && esLaborable(addDias(anterior, -1), feriados)) break;
    inicio = anterior;
    anterior = addDias(anterior, -1);
  }
  return inicio;
}

function subtituloRango(inicio: Date, fin: Date): string {
  const dias: string[] = [];
  for (let d = inicio; d.getTime() <= fin.getTime(); d = addDias(d, 1)) {
    dias.push(NOMBRES_DIA[d.getDay()]);
  }
  if (dias.length <= 1) return "Planificación de Contadores";
  const texto =
    dias.length === 2
      ? `${dias[0]} y ${dias[1]}`
      : `${dias.slice(0, -1).join(", ")} y ${dias[dias.length - 1]}`;
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

/** Rango de "Clientes de hoy": si hoy no es laborable (fin de semana o
 * feriado) no se espera que nadie lo revise, se muestra solo el día.
 * Si es laborable, arranca en el último día no mostrado por nadie
 * (`inicioDeCatchUp`, recupera fines de semana y feriados salteados) y,
 * los viernes, adelanta el sábado (mismo criterio que la card anterior
 * de Inicio, para quien trabaja el sábado y revisa el viernes). */
function rangoHoy(
  now: Date,
  feriados: Set<string>,
): { start: string; end: string; subtitulo: string } {
  if (!esLaborable(now, feriados)) {
    return { start: formatDateLocal(now), end: formatDateLocal(now), subtitulo: "Planificación de Contadores" };
  }
  const inicio = inicioDeCatchUp(now, feriados);
  const fin = now.getDay() === 5 ? addDias(now, 1) : now;
  return { start: formatDateLocal(inicio), end: formatDateLocal(fin), subtitulo: subtituloRango(inicio, fin) };
}

/** Lunes a sábado de la semana en curso, para el heatmap. */
function rangoSemana(now: Date): { start: string; end: string } {
  const lunes = new Date(now.getFullYear(), now.getMonth(), now.getDate() - ((now.getDay() + 6) % 7));
  const sabado = new Date(lunes.getFullYear(), lunes.getMonth(), lunes.getDate() + 5);
  return { start: formatDateLocal(lunes), end: formatDateLocal(sabado) };
}

export function usePendientesResumen(enabled: boolean, refreshKey = 0): Remote<PendientesResumen> {
  return useRemote(enabled, () => pendientesApi.getResumen(), "los pendientes a cerrar", refreshKey);
}

export function useInsumosDashboard(enabled: boolean, refreshKey = 0): Remote<DashboardResponse> {
  return useRemote(enabled, () => insumosApi.getDashboard(), "el dashboard de Insumos", refreshKey);
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

export function useCalendarioHome(enabled: boolean, refreshKey = 0): Remote<CalendarioHome> {
  return useRemote(
    enabled,
    async () => {
      const now = new Date();
      const hoy = formatDateLocal(now);
      const semana = rangoSemana(now);
      const feriados = await gestionApi.listFeriadosPublicos().catch((err: unknown) => {
        // Sin feriados, "hoy" cae al criterio de solo fin de semana (comportamiento previo).
        console.error("Error al consultar feriados:", err);
        return [];
      });
      const feriadosSet = new Set(feriados.map((f) => f.date));
      const rango = rangoHoy(now, feriadosSet);
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
    refreshKey,
  );
}
