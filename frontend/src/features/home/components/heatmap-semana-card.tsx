"use client";

import { Fragment } from "react";
import type { CalendarEvent, Operador } from "@/features/contadores/types/calendario";
import { FALLBACK_COLOR, heatCellStyle } from "../utils/inicio-format";
import { DashboardCard } from "./dashboard-card";

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
function agrupar(eventos: CalendarEvent[], operadores: Operador[]): FilaHeat[] {
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

export function HeatmapSemanaCard({
  eventos,
  operadores,
  loading,
  error,
}: {
  eventos: CalendarEvent[];
  operadores: Operador[];
  loading: boolean;
  error: string | null;
}) {
  const filas = agrupar(eventos, operadores);

  return (
    <DashboardCard
      title="Clientes por operador · semana"
      subtitle="Clientes procesados por día según calendario · si faltan contadores, la facturación queda pendiente"
      loading={loading}
      error={error}
    >
      {filas.length === 0 ? (
        <span className="pt-3 font-body text-[13px] text-muted-foreground">
          No hay clientes planificados esta semana.
        </span>
      ) : (
        <>
          <div className="grid grid-cols-[96px_repeat(6,1fr)] items-center gap-1 pt-3.5">
            <span />
            {DIAS.map((d) => (
              <span
                key={d}
                className="text-center font-heading text-[10px] font-bold text-muted-foreground"
              >
                {d}
              </span>
            ))}
            {filas.map((fila) => (
              <Fragment key={fila.id}>
                <span
                  title={fila.nombre}
                  className="truncate font-body text-[11px] font-semibold"
                  style={{ color: fila.color }}
                >
                  {fila.nombre}
                </span>
                {fila.celdas.map((n, i) => {
                  const estilo = heatCellStyle(n);
                  return (
                    <div
                      key={`${fila.id}-${DIAS[i]}`}
                      title={`${fila.nombre} · ${DIAS[i]}: ${n} ${n === 1 ? "cliente" : "clientes"}`}
                      className="flex h-[26px] items-center justify-center rounded-[5px] font-heading text-[10.5px] font-bold"
                      style={{ background: estilo.bg, color: estilo.text }}
                    >
                      {n > 0 ? n : ""}
                    </div>
                  );
                })}
              </Fragment>
            ))}
          </div>
          <div className="mt-3 flex items-center justify-end gap-1.5">
            <span className="font-body text-[10.5px] text-muted-foreground">menos</span>
            {["rgba(247,148,29,.1)", "rgba(247,148,29,.32)", "rgba(247,148,29,.6)", "#F7941D"].map(
              (bg) => (
                <span key={bg} className="h-3 w-3 rounded-[3px]" style={{ background: bg }} />
              ),
            )}
            <span className="font-body text-[10.5px] text-muted-foreground">más</span>
          </div>
        </>
      )}
    </DashboardCard>
  );
}
