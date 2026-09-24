"use client";

import { useState } from "react";
import { BrandButton } from "@/shared/components/ui/brand-form";
import type { CandidatosEquipo, FilaProyeccion } from "../types/proyeccion";
import { plValida, type Seleccion } from "../hooks/use-candidatos-proyeccion";
import type { useAccionesProyeccion } from "../hooks/use-acciones-proyeccion";
import { n0, tipoEstim } from "./proyeccion-formato";

/** Botonera de `PanelCandidatos.razor` (v1.7):
 * - "Aceptar P/L manual" con una pareja válida; "Aceptar sugerencia" sin
 *   P ni L y con un estimado; si no, "Aceptar" deshabilitado.
 * - "Usar T19 (cascada)" / "Usar entre reales" solo si el backend dice que
 *   el legacy los ofrecería para la fila tal como se ve.
 * - "Marcar pendiente" y "+ Agregar nota" (muestra/oculta la observación,
 *   que viaja con Aceptar P/L y con Marcar pendiente; "Aceptar sugerencia"
 *   la descarta, y no hay acción que guarde la nota sola). */

type Acciones = ReturnType<typeof useAccionesProyeccion>;

interface Props {
  fila: FilaProyeccion;
  datos: CandidatosEquipo | null;
  seleccion: Seleccion;
  acciones: Acciones;
}

function BotonAceptar({ fila, seleccion, acciones, nota }: Omit<Props, "datos"> & { nota: string }) {
  const cargando = acciones.guardando === "aceptar";
  if (seleccion.partida && seleccion.llegada && plValida(seleccion)) {
    return (
      <BrandButton className="flex-1" loading={cargando} onClick={() => acciones.aceptarPL(seleccion, nota)}>
        ✓ Aceptar P/L manual
      </BrandButton>
    );
  }
  if (!seleccion.partida && !seleccion.llegada && !fila.es_real && fila.estim_propuesto !== null) {
    return (
      <BrandButton className="flex-1" loading={cargando} onClick={acciones.aceptarSugerencia}>
        ✓ Aceptar sugerencia
      </BrandButton>
    );
  }
  return (
    <BrandButton className="flex-1" disabled title="Seleccioná P y L para habilitar">
      ✓ Aceptar
    </BrandButton>
  );
}

export function ProyeccionCandidatosAcciones({ fila, datos, seleccion, acciones }: Props) {
  const [mostrarNota, setMostrarNota] = useState(false);
  const [nota, setNota] = useState("");
  const sinPL = !seleccion.partida && !seleccion.llegada;
  const ocupado = acciones.guardando !== null;
  return (
    <div className="flex flex-col gap-2 border-t border-border p-4">
      {sinPL && !fila.es_real && fila.estim_propuesto !== null && (
        <p className="flex justify-between text-[12.5px]">
          <span className="text-muted-foreground">Sugerencia actual</span>
          <span className="font-heading font-extrabold tabular-nums text-brand-orange">
            {n0(fila.estim_propuesto)} <span className="text-xs text-muted-foreground">{tipoEstim(fila.tipo_toma)}</span>
          </span>
        </p>
      )}
      {mostrarNota && (
        <textarea
          value={nota}
          onChange={(e) => setNota(e.target.value)}
          rows={2}
          className="w-full rounded-[8px] border border-border bg-muted p-2 text-xs"
          placeholder="Observación (opcional)…"
        />
      )}
      {acciones.error && <p className="rounded-[6px] bg-destructive/10 px-2 py-1.5 text-xs text-destructive">{acciones.error}</p>}
      <div className="flex flex-wrap gap-2">
        <BotonAceptar fila={fila} seleccion={seleccion} acciones={acciones} nota={nota} />
        {datos?.puede_usar_cascada && (
          <BrandButton variant="outline" loading={acciones.guardando === "cascada_parque"} disabled={ocupado}
            title="Reemplazar la estimación por la cascada de parque (T19)" onClick={() => acciones.forzar("cascada_parque")}>
            ↪ Usar T19 (cascada)
          </BrandButton>
        )}
        {datos?.puede_usar_entre_reales && (
          <BrandButton variant="outline" loading={acciones.guardando === "entre_reales"} disabled={ocupado}
            title="Reemplazar la estimación por la regla de tres entre reales del equipo" onClick={() => acciones.forzar("entre_reales")}>
            ↪ Usar entre reales
          </BrandButton>
        )}
        <BrandButton variant="outline" loading={acciones.guardando === "pendiente"} disabled={ocupado} onClick={() => acciones.marcarPendiente(nota)}>
          ⏸ Marcar pendiente
        </BrandButton>
        <BrandButton variant="outline" onClick={() => setMostrarNota((m) => !m)}>
          {mostrarNota ? "▲ Ocultar nota" : "+ Agregar nota"}
        </BrandButton>
      </div>
    </div>
  );
}
