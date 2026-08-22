"use client";

import { Fragment } from "react";
import type { CalendarEvent, Operador } from "@/features/contadores/types/calendario";
import { FALLBACK_COLOR, heatCellStyle } from "../utils/inicio-format";

const DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"];

interface FilaHeat {
  id: string;
  nombre: string;
  color: string;
  celdas: number[];
  total: number;
}

/** Cuenta clientes por operador × día (Lun..Sáb) a partir de los eventos de
 * la semana. Solo aparecen operadores con al menos un evento. */
export function agruparSemana(eventos: CalendarEvent[], operadores: Operador[]): FilaHeat[] {
  const porOperador = new Map<string, FilaHeat>();
  for (const evt of eventos) {
    if (!evt.operador_id) continue;
    // getDay sobre fecha pura interpretada local: 1=Lun .. 6=Sáb.
    const dia = new Date(`${evt.start.slice(0, 10)}T00:00:00`).getDay();
    if (dia < 1 || dia > 6) continue;
    let fila = porOperador.get(evt.operador_id);
    if (!fila) {
      const op = operadores.find((o) => o.id === evt.operador_id);
      fila = {
        id: evt.operador_id,
        nombre: op?.nombre ?? "Sin nombre",
        color: op?.color ?? FALLBACK_COLOR,
        celdas: Array(6).fill(0) as number[],
        total: 0,
      };
      porOperador.set(evt.operador_id, fila);
    }
    fila.celdas[dia - 1] += 1;
    fila.total += 1;
  }
  return Array.from(porOperador.values()).sort((a, b) => b.total - a.total);
}

/** Heatmap "clientes por operador · semana" (README del handoff): grid
 * `nombre + 6 columnas`, celda con el número, intensidad naranja. Vista pura;
 * la usa la card "Operadores". */
export function HeatmapSemana({
  eventos,
  operadores,
}: {
  eventos: CalendarEvent[];
  operadores: Operador[];
}) {
  const filas = agruparSemana(eventos, operadores);
  if (filas.length === 0) {
    return (
      <span className="font-body text-[12.5px] text-muted-foreground">
        No hay clientes planificados esta semana.
      </span>
    );
  }
  return (
    <div className="flex flex-col">
      <div className="grid grid-cols-[minmax(72px,96px)_repeat(6,minmax(0,1fr))] items-center gap-1">
        <span />
        {DIAS.map((d) => (
          <span
            key={d}
            className="text-center font-heading text-[10.5px] font-bold text-muted-foreground"
          >
            {d}
          </span>
        ))}
        {filas.map((fila) => (
          <Fragment key={fila.id}>
            <span
              title={fila.nombre}
              className="truncate font-body text-[11.5px] font-semibold text-foreground/80"
            >
              {fila.nombre}
            </span>
            {fila.celdas.map((n, i) => {
              const estilo = heatCellStyle(n);
              return (
                <div
                  key={`${fila.id}-${DIAS[i]}`}
                  title={`${fila.nombre} · ${DIAS[i]}: ${n} ${n === 1 ? "cliente" : "clientes"}`}
                  className="flex h-6 items-center justify-center rounded-[5px] font-heading text-[10.5px] font-bold short:h-5"
                  style={{ background: estilo.bg, color: estilo.text }}
                >
                  {n > 0 ? n : ""}
                </div>
              );
            })}
          </Fragment>
        ))}
      </div>
      <div className="mt-1.5 flex items-center justify-end gap-1.5">
        <span className="font-body text-[10.5px] text-muted-foreground">menos</span>
        {["rgba(247,148,29,.14)", "rgba(247,148,29,.38)", "#F7941D"].map((bg) => (
          <span key={bg} className="h-2.5 w-2.5 rounded-[3px]" style={{ background: bg }} />
        ))}
        <span className="font-body text-[10.5px] text-muted-foreground">más</span>
      </div>
    </div>
  );
}
