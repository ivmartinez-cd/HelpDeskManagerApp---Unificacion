"use client";

import { contadoresApi } from "@/features/contadores/api/contadores-api";
import type { CalendarEvent, Operador } from "@/features/contadores/types/calendario";
import { formatDateLocal } from "@/features/contadores/utils/calendario-format";
import { gestionApi } from "@/features/vacaciones/api/gestion-api";
import { useRemote, type Remote } from "./use-inicio-data";

/** Datos de la planificación de Contadores para Inicio (clientes de hoy,
 * pendientes, semana): separado de `use-inicio-data.ts` porque la lógica de
 * rango "hoy" (feriados, fin de semana, look-ahead del viernes) es la parte
 * más larga del feature y merece su propio archivo (§4). */
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
