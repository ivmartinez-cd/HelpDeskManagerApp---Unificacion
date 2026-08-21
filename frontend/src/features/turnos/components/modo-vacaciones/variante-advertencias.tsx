"use client";

import { AlertTriangle, Info, XCircle } from "lucide-react";
import type { AdvertenciaCobertura, FranjaEditable } from "../../types/grilla-variantes";
import { DIAS_SEMANA, type ErrorFranja, type HuecoCobertura } from "../../lib/variante-validacion";
import { formatDiaMes } from "../../lib/variante-estado";

interface VarianteAdvertenciasProps {
  errores: ErrorFranja[];
  huecos: HuecoCobertura[];
  sinOperador: FranjaEditable[];
  /** OPERADOR_AUSENTE: cubrientes con vacaciones aprobadas dentro del rango */
  ausencias: AdvertenciaCobertura[];
  nombreCasilla: (id: string) => string;
}

/** Panel de validación en vivo del editor (ADR-025): los solapes son error y
 * bloquean el guardado; los huecos respecto de la titular, las franjas sin
 * operador y los cubrientes ausentes son advertencias visibles pero no
 * bloquean — un hueco puede ser deliberado. */
export function VarianteAdvertencias({
  errores,
  huecos,
  sinOperador,
  ausencias,
  nombreCasilla,
}: VarianteAdvertenciasProps) {
  if (errores.length + huecos.length + sinOperador.length + ausencias.length === 0) {
    return (
      <p className="flex items-center gap-2 rounded-[10px] border border-border bg-muted/30 px-4 py-3 font-body text-xs text-muted-foreground">
        <Info className="h-4 w-4" />
        Sin solapes ni huecos respecto de la grilla titular.
      </p>
    );
  }
  return (
    <div className="flex flex-col gap-2" aria-live="polite">
      {errores.length > 0 && (
        <ul className="flex flex-col gap-1 rounded-[10px] border border-destructive/20 bg-destructive/10 px-4 py-3">
          {errores.map((e, i) => (
            <li key={i} className="flex items-start gap-2 font-body text-xs text-foreground">
              <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-destructive" />
              <span>{e.mensaje}</span>
            </li>
          ))}
        </ul>
      )}
      {(huecos.length > 0 || sinOperador.length > 0 || ausencias.length > 0) && (
        <ul className="flex flex-col gap-1 rounded-[10px] border border-warning/20 bg-warning/10 px-4 py-3">
          {huecos.map((h, i) => (
            <li key={`h${i}`} className="flex items-start gap-2 font-body text-xs text-foreground">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" />
              <span>
                {nombreCasilla(h.casillaId)} · {DIAS_SEMANA[h.diaSemana]} sin cobertura{" "}
                {h.horaInicio}–{h.horaFin} (la titular sí la cubre)
              </span>
            </li>
          ))}
          {sinOperador.map((f) => (
            <li key={f.key} className="flex items-start gap-2 font-body text-xs text-foreground">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" />
              <span>
                {nombreCasilla(f.casillaId)} · {DIAS_SEMANA[f.diaSemana]} {f.horaInicio}–
                {f.horaFin}: franja sin operador asignado
              </span>
            </li>
          ))}
          {ausencias.map((a, i) => (
            <li key={`a${i}`} className="flex items-start gap-2 font-body text-xs text-foreground">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" />
              <span>
                {a.userName ?? a.userId}:{" "}
                {a.detalle?.startsWith("Horario")
                  ? `${a.detalle.toLowerCase()} aprobado`
                  : `${(a.detalle ?? "Vacaciones").toLowerCase()} aprobada`}{" "}
                del {a.desde ? formatDiaMes(a.desde) : "?"} al{" "}
                {a.hasta ? formatDiaMes(a.hasta) : "?"}
                {a.detalle?.startsWith("Horario")
                  ? ": fuera de ese horario no va a poder cubrir"
                  : ": no va a poder cubrir esos días"}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
