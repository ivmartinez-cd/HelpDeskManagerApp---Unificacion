/** Port de getStatsForYear/getCellStatus del legacy (Absences.tsx): los KPIs
 * y la grilla anual se computan client-side sobre bajas y vacaciones APPROVED
 * del empleado. Fechas como strings YYYY-MM-DD para evitar el off-by-one de
 * toISOString (UTC) del legacy. */

import type { Ausencia, Solicitud, TipoAusencia } from "../types/vacaciones";
import { COLOR_VACACIONES, TIPO_AUSENCIA } from "./tipos-ausencia";

export interface EstadoCelda {
  color: string;
  label: string;
  halfDay: boolean;
  esFeriado: boolean;
}

export interface StatsAsistencia {
  totalBajas: number;
  diasTrabajados: number;
  enfermedad: number;
  vacaciones: number;
  tramitesEstudio: number;
  descuento: number;
  porTipo: Record<TipoAusencia, number>;
}

const pad = (n: number) => String(n).padStart(2, "0");

export const fechaIso = (year: number, month: number, day: number) =>
  `${year}-${pad(month)}-${pad(day)}`;

export const diasDelMes = (year: number, month: number) =>
  new Date(year, month, 0).getDate();

const esFinde = (year: number, month: number, day: number) => {
  const dow = new Date(year, month - 1, day).getDay();
  return dow === 0 || dow === 6;
};

const cubre = (start: string, end: string, fecha: string) =>
  fecha >= start.slice(0, 10) && fecha <= end.slice(0, 10);

export function estadoCelda(
  fecha: string,
  ausencias: Ausencia[],
  vacaciones: Solicitud[],
  feriados: Set<string>,
): EstadoCelda | null {
  if (feriados.has(fecha)) {
    return { color: "#8b5cf6", label: "Feriado", halfDay: false, esFeriado: true };
  }
  const vac = vacaciones.find(
    (v) => v.status === "APPROVED" && cubre(v.startDate, v.endDate, fecha),
  );
  if (vac) {
    return { color: COLOR_VACACIONES, label: "Vacaciones", halfDay: false, esFeriado: false };
  }
  const aus = ausencias.find(
    (a) => a.status === "APPROVED" && cubre(a.startDate, a.endDate, fecha),
  );
  if (aus) {
    return {
      color: TIPO_AUSENCIA[aus.tipo].color,
      label: TIPO_AUSENCIA[aus.tipo].label + (aus.reason ? ` — ${aus.reason}` : ""),
      halfDay: aus.halfDay,
      esFeriado: false,
    };
  }
  return null;
}

export function statsDelAnio(
  year: number,
  ausencias: Ausencia[],
  vacaciones: Solicitud[],
  feriados: Set<string>,
): StatsAsistencia {
  let totalBajas = 0;
  let bajasHabiles = 0;
  let diasHabiles = 0;
  const porTipo = Object.fromEntries(
    Object.keys(TIPO_AUSENCIA).map((t) => [t, 0]),
  ) as Record<TipoAusencia, number>;
  let diasVacaciones = 0;

  for (let month = 1; month <= 12; month++) {
    for (let day = 1; day <= diasDelMes(year, month); day++) {
      const fecha = fechaIso(year, month, day);
      const finde = esFinde(year, month, day);
      const feriado = feriados.has(fecha);
      const habil = !finde && !feriado;
      if (habil) diasHabiles++;

      const vac = vacaciones.find(
        (v) => v.status === "APPROVED" && cubre(v.startDate, v.endDate, fecha),
      );
      if (vac) {
        totalBajas++;
        diasVacaciones++;
        if (habil) bajasHabiles++;
        continue;
      }
      const aus = ausencias.find(
        (a) => a.status === "APPROVED" && cubre(a.startDate, a.endDate, fecha),
      );
      if (!aus) continue;
      const cuenta = aus.halfDay ? 0.5 : 1;
      if (aus.tipo !== "HOME_OFFICE") {
        totalBajas += cuenta;
        if (habil) bajasHabiles += cuenta;
      }
      porTipo[aus.tipo] += aus.tipo === "DESCUENTO_DIA" ? cuenta : 1;
    }
  }

  return {
    totalBajas,
    diasTrabajados: diasHabiles - bajasHabiles,
    enfermedad: porTipo.BAJA_ENFERMEDAD,
    vacaciones: diasVacaciones,
    tramitesEstudio: porTipo.TRAMITE_PERSONAL + porTipo.DIA_ESTUDIO + porTipo.OTHER,
    descuento: porTipo.DESCUENTO_DIA,
    porTipo,
  };
}
