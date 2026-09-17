/** Validación en vivo del editor de grilla variante, espejo de
 * `grilla_variante_reglas.py` (ADR-025): solapes = error bloqueante, huecos
 * respecto de la grilla titular y franjas sin operador = advertencia. El
 * backend revalida todo al guardar; esto solo evita ida y vuelta. */

import type { Slot } from "../types/turnos";
import type { FranjaEditable } from "../types/grilla-variantes";

export interface ErrorFranja {
  /** keys de las franjas involucradas, para resaltarlas */
  keys: string[];
  mensaje: string;
}

export interface HuecoCobertura {
  casillaId: string;
  diaSemana: number;
  /** HH:MM */
  horaInicio: string;
  horaFin: string;
}

export const DIAS_SEMANA = [
  "Lunes",
  "Martes",
  "Miércoles",
  "Jueves",
  "Viernes",
  "Sábado",
  "Domingo",
];

/** "08:30" / "08:30:00" → minutos desde las 0:00. */
export function aMinutos(hhmm: string): number {
  const [h, m] = hhmm.split(":").map(Number);
  return h * 60 + (m || 0);
}

export function aHhmm(minutos: number): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(Math.floor(minutos / 60))}:${pad(minutos % 60)}`;
}

type Intervalo = [number, number];

function unir(intervalos: Intervalo[]): Intervalo[] {
  const unidos: Intervalo[] = [];
  for (const [inicio, fin] of [...intervalos].sort((a, b) => a[0] - b[0])) {
    const ultimo = unidos[unidos.length - 1];
    if (ultimo && inicio <= ultimo[1]) ultimo[1] = Math.max(ultimo[1], fin);
    else unidos.push([inicio, fin]);
  }
  return unidos;
}

function restar(base: Intervalo[], quitar: Intervalo[]): Intervalo[] {
  const resultado: Intervalo[] = [];
  for (const [inicio, fin] of base) {
    let cursor = inicio;
    for (const [qInicio, qFin] of quitar) {
      if (qFin <= cursor || qInicio >= fin) continue;
      if (qInicio > cursor) resultado.push([cursor, qInicio]);
      cursor = Math.max(cursor, qFin);
    }
    if (cursor < fin) resultado.push([cursor, fin]);
  }
  return resultado;
}

function agrupar<T extends { casillaId: string; diaSemana: number }>(items: T[]): Map<string, T[]> {
  const grupos = new Map<string, T[]>();
  for (const item of items) {
    const clave = `${item.casillaId}|${item.diaSemana}`;
    grupos.set(clave, [...(grupos.get(clave) ?? []), item]);
  }
  return grupos;
}

function solapan(a: FranjaEditable, b: FranjaEditable): boolean {
  return aMinutos(a.horaInicio) < aMinutos(b.horaFin) && aMinutos(b.horaInicio) < aMinutos(a.horaFin);
}

/** Errores duros: inicio >= fin, solape en la misma casilla+día. Un operador
 * en dos franjas que se pisan (cualquier casilla, mismo día) es advertencia,
 * no error: ver `advertenciasDeOperadores`. */
export function erroresDeFranjas(
  franjas: FranjaEditable[],
  nombreCasilla: (id: string) => string,
): ErrorFranja[] {
  const errores: ErrorFranja[] = [];
  for (const f of franjas) {
    if (!f.horaInicio || !f.horaFin) {
      errores.push({ keys: [f.key], mensaje: `${nombreCasilla(f.casillaId)}: completá inicio y fin.` });
    } else if (aMinutos(f.horaInicio) >= aMinutos(f.horaFin)) {
      errores.push({
        keys: [f.key],
        mensaje: `${nombreCasilla(f.casillaId)} ${f.horaInicio}–${f.horaFin}: el inicio debe ser menor que el fin.`,
      });
    }
  }
  const validas = franjas.filter(
    (f) => f.horaInicio && f.horaFin && aMinutos(f.horaInicio) < aMinutos(f.horaFin),
  );
  for (const grupo of agrupar(validas).values()) {
    const ordenadas = [...grupo].sort((a, b) => aMinutos(a.horaInicio) - aMinutos(b.horaInicio));
    for (let i = 1; i < ordenadas.length; i++) {
      const prev = ordenadas[i - 1];
      const cur = ordenadas[i];
      if (aMinutos(cur.horaInicio) < aMinutos(prev.horaFin)) {
        errores.push({
          keys: [prev.key, cur.key],
          mensaje: `${nombreCasilla(cur.casillaId)} · ${DIAS_SEMANA[cur.diaSemana]}: ${prev.horaInicio}–${prev.horaFin} y ${cur.horaInicio}–${cur.horaFin} se superponen.`,
        });
      }
    }
  }
  return errores;
}

/** Un mismo operador en dos franjas que se pisan (cualquier casilla, mismo
 * día): no bloquea, puede ser la única cobertura posible (mismo criterio que
 * Coberturas para el reemplazante). */
export function advertenciasDeOperadores(
  franjas: FranjaEditable[],
  nombreCasilla: (id: string) => string,
  nombreUser: (id: string) => string,
): ErrorFranja[] {
  const validas = franjas.filter(
    (f) => f.horaInicio && f.horaFin && aMinutos(f.horaInicio) < aMinutos(f.horaFin),
  );
  const advertencias: ErrorFranja[] = [];
  for (let i = 0; i < validas.length; i++) {
    for (let j = i + 1; j < validas.length; j++) {
      const a = validas[i];
      const b = validas[j];
      if (a.diaSemana !== b.diaSemana || !solapan(a, b)) continue;
      for (const userId of a.userIds.filter((u) => b.userIds.includes(u))) {
        advertencias.push({
          keys: [a.key, b.key],
          mensaje: `${nombreUser(userId)} está en ${nombreCasilla(a.casillaId)} ${a.horaInicio}–${a.horaFin} y en ${nombreCasilla(b.casillaId)} ${b.horaInicio}–${b.horaFin} (${DIAS_SEMANA[a.diaSemana]}).`,
        });
      }
    }
  }
  return advertencias;
}

/** Tramos que la grilla titular cubre y la variante no, por casilla+día. */
export function huecosDeCobertura(
  franjas: FranjaEditable[],
  titular: Slot[],
  diasActivos?: Set<number>,
): HuecoCobertura[] {
  const variante = agrupar(franjas.filter((f) => f.horaInicio && f.horaFin));
  const huecos: HuecoCobertura[] = [];
  for (const [clave, slots] of agrupar(titular)) {
    const [casillaId, diaStr] = clave.split("|");
    const dia = Number(diaStr);
    if (diasActivos && !diasActivos.has(dia)) continue;
    const cubierto = unir(
      (variante.get(clave) ?? []).map((f): Intervalo => [aMinutos(f.horaInicio), aMinutos(f.horaFin)]),
    );
    const base = unir(slots.map((s): Intervalo => [aMinutos(s.horaInicio), aMinutos(s.horaFin)]));
    for (const [inicio, fin] of restar(base, cubierto)) {
      huecos.push({ casillaId, diaSemana: dia, horaInicio: aHhmm(inicio), horaFin: aHhmm(fin) });
    }
  }
  return huecos;
}

export function franjasSinOperador(franjas: FranjaEditable[]): FranjaEditable[] {
  return franjas.filter((f) => f.userIds.length === 0);
}


export function diasActivosDeRango(desde: string, hasta: string): Set<number> | undefined {
  if (!desde || !hasta) return undefined;
  const dDesde = new Date(desde + "T12:00:00");
  const dHasta = new Date(hasta + "T12:00:00");
  const diffDays = Math.round((dHasta.getTime() - dDesde.getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays < 6) {
    const set = new Set<number>();
    for (let i = 0; i <= diffDays; i++) {
      const d = new Date(dDesde.getTime() + i * 24 * 60 * 60 * 1000);
      const day = d.getDay();
      set.add(day === 0 ? 6 : day - 1);
    }
    return set;
  }
  return undefined;
}

/** "2026-09-15" → 0=lunes … 6=domingo (fecha local, no UTC). */
export function diaSemanaDeIso(iso: string): number {
  const d = new Date(iso + "T12:00:00").getDay();
  return d === 0 ? 6 : d - 1;
}

/** Día en el que conviene pararse al abrir editor/preview: hoy si el rango lo
 * alcanza, si no el primer día que sí aplica. `diasActivos` undefined (rango
 * de una semana o más) = todos los días aplican. */
export function diaInicialVigente(
  diasActivos: Set<number> | undefined,
  hoyDia: number,
  disponibles?: number[],
): number {
  const candidatos = (disponibles ?? [0, 1, 2, 3, 4, 5, 6]).filter(
    (d) => !diasActivos || diasActivos.has(d),
  );
  if (candidatos.length === 0) return disponibles?.[0] ?? hoyDia;
  return candidatos.includes(hoyDia) ? hoyDia : candidatos[0];
}
