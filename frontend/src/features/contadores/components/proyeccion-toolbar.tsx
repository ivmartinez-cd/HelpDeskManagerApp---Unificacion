"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import type { FilaProyeccion } from "../types/proyeccion";

/** Toolbar de la grilla (`GrillaEstimacion.razor` v1.7): chips de filtro con
 * sus conteos, búsqueda y el menú "Exportar CSV ▾" (Todos / Solo estimados). */

export type FiltroChip = "todos" | "estimar" | "reales" | "sospechosos";

export function aplicaFiltro(fila: FilaProyeccion, filtro: FiltroChip): boolean {
  if (filtro === "estimar") return !fila.es_real;
  if (filtro === "reales") return fila.es_real;
  if (filtro === "sospechosos") return fila.borde_salto_imposible;
  return true;
}

/** Nro. de serie, empresa, sucursal o sector (sin distinguir mayúsculas). */
export function coincideBusqueda(fila: FilaProyeccion, termino: string): boolean {
  const q = termino.trim().toLowerCase();
  if (!q) return true;
  return [fila.nro_serie, fila.empresa, fila.sucursal, fila.sector].some((t) => t.toLowerCase().includes(q));
}

const FILTROS: { value: FiltroChip; label: string }[] = [
  { value: "todos", label: "Todos" },
  { value: "estimar", label: "A estimar" },
  { value: "reales", label: "Reales" },
  { value: "sospechosos", label: "Sospechosos" },
];

interface ExportProps {
  visible: boolean;
  habilitado: boolean;
  exportando: boolean;
  totalFilas: number;
  estimados: number;
  onExportar: (soloEstimados: boolean) => void;
}

interface ProyeccionToolbarProps {
  filas: FilaProyeccion[];
  filtro: FiltroChip;
  onFiltro: (f: FiltroChip) => void;
  busqueda: string;
  onBusqueda: (q: string) => void;
  exportar: ExportProps;
}

export function ProyeccionToolbar({ filas, filtro, onFiltro, busqueda, onBusqueda, exportar }: ProyeccionToolbarProps) {
  const contar = (f: FiltroChip) => filas.filter((fila) => aplicaFiltro(fila, f)).length;
  return (
    <div className="flex flex-wrap items-end gap-3">
      <SegmentedControl
        options={FILTROS.map((f) => ({ value: f.value, label: `${f.label} (${contar(f.value)})` }))}
        value={filtro}
        onChange={(v) => onFiltro(v as FiltroChip)}
      />
      <div className="min-w-[260px]">
        <BrandInput
          label="Buscar"
          type="search"
          placeholder="Buscar nro serie / sucursal / sector…"
          value={busqueda}
          onChange={(e) => onBusqueda(e.target.value)}
        />
      </div>
      {exportar.visible && <MenuExport {...exportar} />}
    </div>
  );
}

function MenuExport({ habilitado, exportando, totalFilas, estimados, onExportar }: ExportProps) {
  const [abierto, setAbierto] = useState(false);
  const elegir = (soloEstimados: boolean) => {
    setAbierto(false);
    onExportar(soloEstimados);
  };
  return (
    <div className="relative ml-auto">
      <BrandButton
        variant="outline"
        loading={exportando}
        disabled={!habilitado || exportando}
        title={habilitado ? "Exportar CSV del proceso" : "Elegí un grupo económico y un proceso real para exportar"}
        onClick={() => setAbierto((a) => !a)}
      >
        {exportando ? "Exportando…" : "Exportar CSV"}
        <ChevronDown className="ml-1 h-3.5 w-3.5" />
      </BrandButton>
      {abierto && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setAbierto(false)} />
          <div className="absolute right-0 z-20 mt-1 min-w-[200px] overflow-hidden rounded-[8px] border border-border bg-card shadow-lg">
            <OpcionExport label="Todos" cantidad={totalFilas} onClick={() => elegir(false)} />
            <OpcionExport label="Solo estimados" cantidad={estimados} onClick={() => elegir(true)} />
          </div>
        </>
      )}
    </div>
  );
}

function OpcionExport({ label, cantidad, onClick }: { label: string; cantidad: number; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex w-full items-center justify-between gap-4 px-4 py-2 text-left text-sm hover:bg-muted"
    >
      {label}
      <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-semibold tabular-nums text-muted-foreground">
        {cantidad}
      </span>
    </button>
  );
}
