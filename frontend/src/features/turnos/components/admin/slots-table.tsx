"use client";

import { Plus, Trash2, Users } from "lucide-react";
import type { Dispatch, SetStateAction } from "react";
import { Button } from "@/shared/components/ui/button";
import { SortableHeader, type SortableColumn } from "@/shared/components/ui/sortable-header";
import { useOptionalTableSort, useSortedRows } from "@/shared/hooks/use-optional-table-sort";
import type { Slot } from "../../types/turnos";

const DIAS_SEMANA = [
  "Lunes",
  "Martes",
  "Miércoles",
  "Jueves",
  "Viernes",
  "Sábado",
  "Domingo",
];

type SortKey = "inicio" | "fin" | "operadores";

const COLUMNAS: SortableColumn<SortKey>[] = [
  { key: "inicio", label: "Hora Inicio" },
  { key: "fin", label: "Hora Fin" },
  // Por cantidad de operadores: deja a mano las franjas sin cubrir.
  { key: "operadores", label: "Operadores Asignados" },
];

const DESC_PRIMERO: readonly SortKey[] = ["operadores"];

function valorOrden(s: Slot, key: SortKey) {
  switch (key) {
    case "inicio": return s.horaInicio;
    case "fin": return s.horaFin;
    case "operadores": return s.asignaciones.length;
  }
}

interface Props {
  selectedDia: number;
  setSelectedDia: Dispatch<SetStateAction<number>>;
  activeSlots: Slot[];
  puedeEditar: boolean;
  onAddSlot: () => void;
  onEditSlot: (slot: Slot) => void;
  onDeleteSlot: (id: string) => void;
}

/** Selector de día + tabla de franjas horarias de la casilla seleccionada,
 * extraído de `casillas-manager.tsx` (§4). */
export function SlotsTable({
  selectedDia, setSelectedDia, activeSlots, puedeEditar, onAddSlot, onEditSlot, onDeleteSlot,
}: Props) {
  const { sort, toggleSort } = useOptionalTableSort(DESC_PRIMERO);
  const filas = useSortedRows(activeSlots, sort, valorOrden);
  return (
    <div className="flex flex-col gap-4">
      {/* Días de la semana */}
      <div className="flex flex-wrap items-center gap-1 border-b border-border/50 pb-2">
        {DIAS_SEMANA.map((dia, idx) => (
          <button
            key={dia}
            onClick={() => setSelectedDia(idx)}
            className={`rounded-[6px] px-3 py-1.5 font-body text-xs font-semibold transition-colors ${
              selectedDia === idx
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-muted"
            }`}
          >
            {dia}
          </button>
        ))}
      </div>

      {/* Tabla de Franjas Horarias */}
      <div className="flex items-center justify-between">
        <span className="font-heading text-sm font-bold text-foreground">
          Horarios para {DIAS_SEMANA[selectedDia]}
        </span>
        {puedeEditar && (
          <Button onClick={onAddSlot} size="sm" variant="outline" className="gap-1.5">
            <Plus className="h-3.5 w-3.5" />
            Agregar Franja
          </Button>
        )}
      </div>

      <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
        <table className="w-full text-left font-body text-xs">
          <thead className="border-b border-border bg-muted/50 font-heading text-muted-foreground">
            <tr>
              {COLUMNAS.map((c) => (
                <SortableHeader
                  key={c.key}
                  column={c}
                  sort={sort}
                  onToggleSort={toggleSort}
                  thClassName="p-3 font-semibold"
                />
              ))}
              <th className="p-3 text-right font-semibold">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {activeSlots.length > 0 ? (
              filas.map((s) => (
                <tr key={s.id} className="hover:bg-muted/30">
                  <td className="p-3 font-mono font-medium">{s.horaInicio.slice(0, 5)}</td>
                  <td className="p-3 font-mono font-medium">{s.horaFin.slice(0, 5)}</td>
                  <td className="p-3">
                    <div className="flex flex-wrap gap-1">
                      {s.asignaciones.length > 0 ? (
                        s.asignaciones.map((a) => (
                          <span
                            key={a.id}
                            className="rounded-full bg-brand-orange/10 text-brand-orange border border-brand-orange/20 px-2.5 py-0.5 font-medium"
                          >
                            {a.userName || "Desconocido"}
                          </span>
                        ))
                      ) : (
                        <span className="italic text-muted-foreground">Sin operadores</span>
                      )}
                    </div>
                  </td>
                  <td className="p-3 text-right">
                    {puedeEditar && (
                      <div className="flex justify-end items-center gap-2">
                        <button
                          onClick={() => onEditSlot(s)}
                          className="p-1 text-muted-foreground hover:text-foreground"
                          title="Editar franja/asignaciones"
                        >
                          <Users className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => onDeleteSlot(s.id)}
                          className="p-1 text-muted-foreground hover:text-destructive"
                          title="Eliminar franja"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4} className="p-6 text-center text-muted-foreground">
                  No hay horarios configurados para este día.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
