"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import { useOptionalTableSort, useSortedRows } from "@/shared/hooks/use-optional-table-sort";
import type { FilaProyeccion } from "../types/proyeccion";
import { compararEsAr, n0, TEC_LABEL } from "./proyeccion-formato";

/** "Detalle por Modelo" de `GrillaEstimacion.razor` (v1.7), colapsado por
 * defecto: por modelo, equipos, impresiones del período por clase, promedio
 * por equipo y mediana truncada P80, discriminando mono/color según el modo
 * de operación (Cl.20 total en ModoOper 2/4, solo color en 3/5).
 *
 * Necesita que el backend exponga `id_art_gen` e `id_modo_oper` en la fila:
 * mientras no vengan, la sección no se muestra (no se inventa el modo). Un
 * `ID_ModoOper` NULL sí se muestra: como en el legacy no es "Cl.20 total",
 * así que discrimina mono/color. */

const MODOS_CL20_TOTAL = new Set([2, 4]);

/** `MedianaTruncadaP80` del legacy: N≤1 sin dato; N=2..4 mediana cruda;
 * N≥5 mediana del 80% más bajo. */
export function medianaTruncadaP80(valores: number[]): number | null {
  if (valores.length <= 1) return null;
  const ord = [...valores].sort((a, b) => a - b);
  const base = ord.length < 5 ? ord : ord.slice(0, Math.ceil(ord.length * 0.8));
  const mid = Math.floor(base.length / 2);
  return base.length % 2 === 1 ? base[mid] : (base[mid - 1] + base[mid]) / 2;
}

interface FilaDetalle {
  modelo: string;
  tec: string;
  equipos: number;
  imp10: number;
  imp20: number;
  promMono: number | null;
  promColor: number | null;
  medMono: number | null;
  medColor: number | null;
  medTotal: number | null;
}

function impDe(filas: FilaProyeccion[], clase: string): number {
  return filas.filter((f) => f.clase === clase).reduce((s, f) => s + (f.impresiones ?? 0), 0);
}

function porMaquina(filas: FilaProyeccion[]): FilaProyeccion[][] {
  const m = new Map<number, FilaProyeccion[]>();
  for (const f of filas) m.set(f.id_maquina, [...(m.get(f.id_maquina) ?? []), f]);
  return [...m.values()];
}

function detalleDe(filas: FilaProyeccion[]): FilaDetalle {
  const sample = filas[0];
  const maquinas = porMaquina(filas);
  const n = maquinas.length;
  const mono = maquinas.map((mg) => impDe(mg, "10"));
  const color = maquinas.map((mg) => impDe(mg, "20"));
  const imp10 = impDe(filas, "10");
  const imp20 = impDe(filas, "20");
  const esMono = sample.tecnologia === "MONO";
  const discrimina = !esMono && !MODOS_CL20_TOTAL.has(sample.id_modo_oper ?? 0);
  return {
    modelo: sample.modelo,
    tec: TEC_LABEL[sample.tecnologia],
    equipos: n,
    imp10,
    imp20,
    promMono: esMono || discrimina ? imp10 / n : null,
    promColor: discrimina ? imp20 / n : null,
    medMono: esMono || discrimina ? medianaTruncadaP80(mono) : null,
    medColor: discrimina ? medianaTruncadaP80(color) : null,
    medTotal: medianaTruncadaP80(mono.map((v, i) => v + color[i])),
  };
}

function agruparPorModelo(filas: FilaProyeccion[]): FilaDetalle[] {
  const m = new Map<number, FilaProyeccion[]>();
  for (const f of filas) m.set(f.id_art_gen ?? 0, [...(m.get(f.id_art_gen ?? 0) ?? []), f]);
  return [...m.values()].map(detalleDe).sort((a, b) => compararEsAr(a.modelo, b.modelo));
}

const promTotal = (d: FilaDetalle) => (d.equipos > 0 ? (d.imp10 + d.imp20) / d.equipos : 0);

type SortKey = keyof FilaDetalle | "impTotal" | "promTotal";

/** Encabezados en el orden de la tabla, con el valor por el que ordena cada uno. */
const COLUMNAS: { key: SortKey; label: string; valor: (d: FilaDetalle) => string | number | null }[] = [
  { key: "modelo", label: "Modelo", valor: (d) => d.modelo },
  { key: "tec", label: "Tec.", valor: (d) => d.tec },
  { key: "equipos", label: "Equipos", valor: (d) => d.equipos },
  { key: "imp10", label: "Imp. Período (Cl. 10)", valor: (d) => d.imp10 },
  { key: "imp20", label: "Imp. Período (Cl. 20)", valor: (d) => d.imp20 },
  { key: "impTotal", label: "Imp. Período (Total)", valor: (d) => d.imp10 + d.imp20 },
  { key: "promMono", label: "Prom. Mono", valor: (d) => d.promMono },
  { key: "promColor", label: "Prom. Color", valor: (d) => d.promColor },
  { key: "promTotal", label: "Prom. Total", valor: promTotal },
  { key: "medMono", label: "Med. P80 Mono", valor: (d) => d.medMono },
  { key: "medColor", label: "Med. P80 Color", valor: (d) => d.medColor },
  { key: "medTotal", label: "Med. P80 Total", valor: (d) => d.medTotal },
];

const DESC_PRIMERO: readonly SortKey[] = COLUMNAS.slice(2).map((c) => c.key);

function valorOrden(d: FilaDetalle, key: SortKey) {
  return COLUMNAS.find((c) => c.key === key)?.valor(d);
}

const guion = (v: number | null) => (v === null ? "—" : n0(v));
const siPositivo = (v: number) => (v > 0 ? n0(v) : "—");

export function ProyeccionDetalleModelo({ filas }: { filas: FilaProyeccion[] }) {
  const [abierto, setAbierto] = useState(false);
  const { sort, toggleSort } = useOptionalTableSort(DESC_PRIMERO);
  const disponible = filas.length > 0 && filas.every((f) => f.id_art_gen !== undefined && f.id_modo_oper !== undefined);
  const detalle = useSortedRows(disponible ? agruparPorModelo(filas) : [], sort, valorOrden);
  if (!disponible) return null;
  const totEquipos = detalle.reduce((s, d) => s + d.equipos, 0);
  const tot10 = detalle.reduce((s, d) => s + d.imp10, 0);
  const tot20 = detalle.reduce((s, d) => s + d.imp20, 0);
  const totMed = medianaTruncadaP80(porMaquina(filas).map((mg) => mg.reduce((s, f) => s + (f.impresiones ?? 0), 0)));
  return (
    <section className="rounded-[12px] border border-border bg-card">
      <button
        type="button"
        onClick={() => setAbierto((a) => !a)}
        className="flex w-full items-center gap-2 px-4 py-3 text-left"
      >
        {abierto ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        <span className="font-heading text-sm font-bold">Detalle por Modelo</span>
        <span className="text-xs text-muted-foreground">
          Cantidad de equipos · impresiones del periodo · promedio por equipo · mediana truncada P80
        </span>
      </button>
      {abierto && (
        <div className="overflow-x-auto border-t border-border">
          <table className="w-full min-w-[980px] text-right text-xs tabular-nums">
            <thead className="text-[10px] font-bold uppercase text-muted-foreground">
              <tr>
                {COLUMNAS.map((c, i) => (
                  <SortableHeader
                    key={c.key}
                    column={c}
                    sort={sort}
                    onToggleSort={toggleSort}
                    thClassName={i < 2 ? "px-3 py-2 text-left" : "px-3 py-2"}
                  />
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {detalle.map((d) => (
                <tr key={`${d.modelo}-${d.tec}`}>
                  <td className="px-3 py-1.5 text-left">{d.modelo}</td>
                  <td className="px-3 py-1.5 text-left">{d.tec}</td>
                  <td className="px-3 py-1.5">{d.equipos}</td>
                  <td className="px-3 py-1.5">{siPositivo(d.imp10)}</td>
                  <td className="px-3 py-1.5">{siPositivo(d.imp20)}</td>
                  <td className="px-3 py-1.5">{n0(d.imp10 + d.imp20)}</td>
                  <td className="px-3 py-1.5">{guion(d.promMono)}</td>
                  <td className="px-3 py-1.5">{guion(d.promColor)}</td>
                  <td className="px-3 py-1.5">{n0(promTotal(d))}</td>
                  <td className="px-3 py-1.5">{guion(d.medMono)}</td>
                  <td className="px-3 py-1.5">{guion(d.medColor)}</td>
                  <td className="px-3 py-1.5">{guion(d.medTotal)}</td>
                </tr>
              ))}
              <tr className="font-bold">
                <td className="px-3 py-1.5 text-left" colSpan={2}>TOTAL proceso</td>
                <td className="px-3 py-1.5">{totEquipos}</td>
                <td className="px-3 py-1.5">{siPositivo(tot10)}</td>
                <td className="px-3 py-1.5">{siPositivo(tot20)}</td>
                <td className="px-3 py-1.5">{n0(tot10 + tot20)}</td>
                <td className="px-3 py-1.5">—</td>
                <td className="px-3 py-1.5">—</td>
                <td className="px-3 py-1.5">{n0(totEquipos > 0 ? (tot10 + tot20) / totEquipos : 0)}</td>
                <td className="px-3 py-1.5">—</td>
                <td className="px-3 py-1.5">—</td>
                <td className="px-3 py-1.5">{guion(totMed)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
