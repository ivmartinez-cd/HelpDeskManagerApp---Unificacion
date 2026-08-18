/** Armado de la grilla mensual (lunes a domingo) con strings YYYY-MM-DD. */

import type { EventoCalendario } from "../types/vacaciones";

export interface GridDay {
  iso: string;
  day: number;
  inMonth: boolean;
  isToday: boolean;
  isWeekend: boolean;
}

export const WEEKDAY_LABELS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"];

const MESES = [
  "enero",
  "febrero",
  "marzo",
  "abril",
  "mayo",
  "junio",
  "julio",
  "agosto",
  "septiembre",
  "octubre",
  "noviembre",
  "diciembre",
];

export function labelMes(year: number, month: number): string {
  return `${MESES[month - 1]} de ${year}`;
}

function toIso(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function buildGridDays(year: number, month: number, hoyIso: string): GridDay[] {
  const primero = new Date(year, month - 1, 1);
  // Lunes = 0 en nuestra grilla (getDay: 0=domingo).
  const offset = (primero.getDay() + 6) % 7;
  const inicio = new Date(year, month - 1, 1 - offset);
  const celdas: GridDay[] = [];
  for (let i = 0; i < 42; i++) {
    const fecha = new Date(inicio.getFullYear(), inicio.getMonth(), inicio.getDate() + i);
    const iso = toIso(fecha);
    const dow = fecha.getDay();
    celdas.push({
      iso,
      day: fecha.getDate(),
      inMonth: fecha.getMonth() === month - 1,
      isToday: iso === hoyIso,
      isWeekend: dow === 0 || dow === 6,
    });
  }
  // Si la última fila es toda del mes siguiente, se recorta (5 filas).
  const ultimaFila = celdas.slice(35);
  return ultimaFila.every((c) => !c.inMonth) ? celdas.slice(0, 35) : celdas;
}

/** Eventos de vacaciones que cubren un día dado (end del wire es exclusivo). */
export function eventosDelDia(
  eventos: EventoCalendario[],
  iso: string,
): EventoCalendario[] {
  return eventos.filter((e) => e.tipo === "vacation" && e.start <= iso && iso < e.end);
}

export function feriadoDelDia(
  eventos: EventoCalendario[],
  iso: string,
): EventoCalendario | undefined {
  return eventos.find((e) => e.tipo === "holiday" && e.start === iso);
}

/** Rango de la grilla visible (lunes a domingo), no del mes calendario: la
 * grilla siempre muestra días de fin del mes anterior/inicio del siguiente
 * para completar semanas, y esos eventos también hay que pedirlos. */
export function rangoDeGrilla(year: number, month: number): { desde: string; hasta: string } {
  const celdas = buildGridDays(year, month, "");
  return { desde: celdas[0].iso, hasta: celdas[celdas.length - 1].iso };
}
