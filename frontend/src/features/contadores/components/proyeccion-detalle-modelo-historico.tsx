"use client";

import { Fragment, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
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

function Encabezado() {
  return (
    <thead className="text-[10px] font-bold uppercase text-muted-foreground">
      <tr>
        <th rowSpan={2} className="px-3 py-2 text-left">Modelo</th>
        <th rowSpan={2} className="px-3 py-2 text-left">Clase</th>
        <th rowSpan={2} className="px-3 py-2">Equipos (proceso)</th>
        {NIVELES.map((n) => (
          <th key={n.clave} colSpan={3} className="border-l border-border px-3 py-2 text-center">{n.titulo}</th>
        ))}
      </tr>
      <tr>
        {NIVELES.map((n) => (
          <Fragment key={n.clave}>
            <th className="border-l border-border px-3 py-1">N</th>
            <th className="px-3 py-1">Med. P80</th>
            <th className="px-3 py-1">Cruda</th>
          </Fragment>
        ))}
      </tr>
    </thead>
  );
}

export function ProyeccionDetalleModeloHistorico({ filas }: { filas: FilaProyeccion[] }) {
  const [abierto, setAbierto] = useState(false);
  const faltanDatos = filas.some(
    (f) => f.id_art_gen === undefined || f.id_modo_oper === undefined || f.parque_historico == null,
  );
  if (filas.length === 0 || faltanDatos) return null;
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
            <Encabezado />
            <tbody className="divide-y divide-border">
              {agrupar(filas).map((f) => (
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
