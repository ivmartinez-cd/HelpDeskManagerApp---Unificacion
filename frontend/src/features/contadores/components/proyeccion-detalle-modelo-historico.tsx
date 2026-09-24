"use client";

import { Fragment, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import type { SortDirection } from "@/shared/hooks/use-table-sort";
import { useOptionalTableSort, useSortedRows } from "@/shared/hooks/use-optional-table-sort";
import type { FilaProyeccion, NivelParque, ParqueHistorico } from "../types/proyeccion";
import { compararEsAr, n0 } from "./proyeccion-formato";

/** "Detalle por Modelo histórico" de `GrillaEstimacion.razor` (v1.7),
 * colapsado por defecto: los valores de parque que alimentan la cascada
 * (T19), una fila por (modelo, modo de operación, clase). Por nivel: N
 * equipos, mediana truncada P80 (el valor que usa el motor) y mediana
 * cruda de referencia.
 *
 * Necesita que el backend exponga `id_art_gen`, `id_modo_oper` y
 * `parque_historico` en la fila: mientras no vengan, no se muestra. */

const MODOS_CL20_TOTAL = new Set([2, 4]);

const NIVELES: { clave: keyof ParqueHistorico; titulo: string }[] = [
  { clave: "cliente_modelo", titulo: "Cliente · Modelo" },
  { clave: "grupo_modelo", titulo: "Grupo · Modelo" },
  { clave: "cliente_tec", titulo: "Cliente · Tec" },
  { clave: "global_modelo", titulo: "Global · Modelo" },
];

interface FilaHist {
  clave: string;
  modelo: string;
  clase: string;
  equipos: number;
  parque: ParqueHistorico;
}

function claseHist(f: FilaProyeccion): string {
  if (f.clase === "10") return "Mono";
  return MODOS_CL20_TOTAL.has(f.id_modo_oper ?? 0) ? "Total" : "Color";
}

function agrupar(filas: FilaProyeccion[]): FilaHist[] {
  const grupos = new Map<string, FilaProyeccion[]>();
  for (const f of filas) {
    const clave = `${f.id_art_gen ?? 0}|${f.id_modo_oper ?? 0}|${f.clase}`;
    grupos.set(clave, [...(grupos.get(clave) ?? []), f]);
  }
  return [...grupos.entries()]
    .map(([clave, g]) => ({
      clave,
      modelo: g[0].modelo,
      clase: claseHist(g[0]),
      equipos: new Set(g.map((f) => f.id_maquina)).size,
      parque: g[0].parque_historico!,
    }))
    .sort((a, b) => compararEsAr(a.modelo, b.modelo) || compararEsAr(a.clase, b.clase));
}

type Medida = "n" | "p80" | "cruda";
type SortKey = "modelo" | "clase" | "equipos" | `${keyof ParqueHistorico}:${Medida}`;

const MEDIDAS: { medida: Medida; label: string }[] = [
  { medida: "n", label: "N" },
  { medida: "p80", label: "Med. P80" },
  { medida: "cruda", label: "Cruda" },
];

/** Todas menos Modelo y Clase arrancan de mayor a menor. */
const DESC_PRIMERO: readonly SortKey[] = [
  "equipos",
  ...NIVELES.flatMap((n) => MEDIDAS.map((m) => `${n.clave}:${m.medida}` as const)),
];

function valorOrden(f: FilaHist, key: SortKey) {
  if (key === "modelo" || key === "clase" || key === "equipos") return f[key];
  const [nivel, medida] = key.split(":") as [keyof ParqueHistorico, Medida];
  return f.parque[nivel][medida];
}

interface OrdenProps {
  sort: { key: SortKey | null; direction: SortDirection };
  onToggleSort: (key: SortKey) => void;
}

// `Ni`: 0 equipos → "—".
const ni = (n: number) => (n > 0 ? n0(n) : "—");

function CeldasNivel({ nivel }: { nivel: NivelParque }) {
  return (
    <>
      <td className="border-l border-border px-3 py-1.5">{ni(nivel.n)}</td>
      <td className="px-3 py-1.5">{n0(nivel.p80)}</td>
      <td className="px-3 py-1.5">{n0(nivel.cruda)}</td>
    </>
  );
}

function Encabezado(orden: OrdenProps) {
  const col = (key: SortKey, label: string, thClassName: string, rowSpan?: number) => (
    <SortableHeader key={key} column={{ key, label }} {...orden} thClassName={thClassName} rowSpan={rowSpan} />
  );
  return (
    <thead className="text-[10px] font-bold uppercase text-muted-foreground">
      <tr>
        {col("modelo", "Modelo", "px-3 py-2 text-left", 2)}
        {col("clase", "Clase", "px-3 py-2 text-left", 2)}
        {col("equipos", "Equipos (proceso)", "px-3 py-2", 2)}
        {NIVELES.map((n) => (
          <th key={n.clave} colSpan={3} className="border-l border-border px-3 py-2 text-center">{n.titulo}</th>
        ))}
      </tr>
      <tr>
        {NIVELES.map((n) => (
          <Fragment key={n.clave}>
            {MEDIDAS.map((m, i) =>
              col(`${n.clave}:${m.medida}`, m.label, i === 0 ? "border-l border-border px-3 py-1" : "px-3 py-1"),
            )}
          </Fragment>
        ))}
      </tr>
    </thead>
  );
}

export function ProyeccionDetalleModeloHistorico({ filas }: { filas: FilaProyeccion[] }) {
  const [abierto, setAbierto] = useState(false);
  const { sort, toggleSort } = useOptionalTableSort(DESC_PRIMERO);
  const faltanDatos = filas.some(
    (f) => f.id_art_gen === undefined || f.id_modo_oper === undefined || f.parque_historico == null,
  );
  const disponible = filas.length > 0 && !faltanDatos;
  const filasHist = useSortedRows(disponible ? agrupar(filas) : [], sort, valorOrden);
  if (!disponible) return null;
  return (
    <section className="rounded-[12px] border border-border bg-card">
      <button type="button" onClick={() => setAbierto((a) => !a)} className="flex w-full items-center gap-2 px-4 py-3 text-left">
        {abierto ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        <span className="font-heading text-sm font-bold">Detalle por Modelo histórico</span>
        <span className="text-xs text-muted-foreground">
          Valores de parque que alimentan la cascada de estimación (T19): por nivel, N equipos · mediana truncada P80
          (valor usado) · mediana cruda (ref). Una fila por modelo y clase.
        </span>
      </button>
      {abierto && (
        <div className="overflow-x-auto border-t border-border">
          <table className="w-full min-w-[1100px] text-right text-xs tabular-nums">
            <Encabezado sort={sort} onToggleSort={toggleSort} />
            <tbody className="divide-y divide-border">
              {filasHist.map((f) => (
                <tr key={f.clave}>
                  <td className="px-3 py-1.5 text-left">{f.modelo}</td>
                  <td className="px-3 py-1.5 text-left">{f.clase}</td>
                  <td className="px-3 py-1.5">{f.equipos}</td>
                  {NIVELES.map((n) => <CeldasNivel key={n.clave} nivel={f.parque[n.clave]} />)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
