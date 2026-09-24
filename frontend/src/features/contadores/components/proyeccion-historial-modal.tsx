"use client";

import { Fragment, useEffect, useState } from "react";
import { X } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import { mensajeError, proyeccionApi } from "../api/proyeccion-api";
import type { FilaProyeccion, HistorialLectura } from "../types/proyeccion";
import { fechaLarga, n0, TEC_LABEL } from "./proyeccion-formato";
import { colorPunto, esTipoReal, HistorialChart, validacionHistorial } from "./proyeccion-historial-chart";

/** Línea de tiempo de un equipo — paridad con `DrillDownModal` legacy. Solo
 * lectura: para editar Partida/Llegada se usa el panel de candidatos (ícono
 * de ojo). Identidad del equipo viene de la fila que abrió el modal — ya la
 * tiene la tabla, evita duplicar la consulta de metadata contra Siges. */

/** `ClaseDesc` del legacy: la clase según el modo de operación (Cl.20 es
 * total en ModoOper 2/4 y solo color en 3/5). Sin el modo, "color". */
function claseDesc(fila: FilaProyeccion): string {
  const modo = fila.id_modo_oper ?? null;
  if (fila.clase === "10") return "mono";
  if (fila.clase === "20") {
    if (modo === 2 || modo === 4) return "total (mono+color)";
    if (modo === 3 || modo === 5) return "solo color";
    return "color";
  }
  if (fila.clase === "30") return "digitalización";
  return `clase ${fila.clase}`;
}

const LEYENDA: { color: string; label: string }[] = [
  { color: "#16a34a", label: "Real" },
  { color: "#ea580c", label: "Estimado" },
  { color: "#ca8a04", label: "T4 (ST)" },
  { color: "#2563eb", label: "Inicial / Reinicial" },
];

export function ProyeccionHistorialModal({ fila, onClose }: { fila: FilaProyeccion; onClose: () => void }) {
  const [lecturas, setLecturas] = useState<HistorialLectura[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    proyeccionApi
      .getHistorialEquipo(fila.id_maquina, fila.clase)
      .then((r) => setLecturas(r.lecturas))
      .catch((err) => setError(`Error al cargar el historial: ${mensajeError(err, "falló la conexión")}`));
  }, [fila.id_maquina, fila.clase]);

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div
        className="flex max-h-[90vh] w-full max-w-[920px] flex-col overflow-hidden rounded-[12px] bg-card shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start gap-3 border-b border-border px-6 py-4">
          <div className="flex-1">
            <h2 className="flex items-center gap-2 font-heading text-lg font-extrabold text-foreground">
              {fila.nro_serie}
              <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-bold uppercase text-muted-foreground">
                {TEC_LABEL[fila.tecnologia]}
              </span>
              <span
                className="text-[10px] font-bold text-muted-foreground"
                title="Clase de contador y semántica según ModoOper"
              >
                Cl. {fila.clase} · {claseDesc(fila)}
              </span>
            </h2>
            <p className="text-xs text-muted-foreground">
              {fila.modelo} · {fila.empresa} · {fila.sucursal}
              {fila.sector && ` · ${fila.sector}`}
            </p>
          </div>
          <button type="button" onClick={onClose} title="Cerrar" className="text-muted-foreground hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="overflow-y-auto px-6 py-5">
          {error && <p className="text-sm text-destructive">⚠ {error}</p>}
          {!error && lecturas === null && <p className="text-sm text-muted-foreground">Cargando historial…</p>}
          {lecturas && (
            <>
              <p className="mb-2 text-xs font-bold uppercase tracking-wide text-muted-foreground">
                Contador e impresiones por período — últimos 24 meses
              </p>
              <HistorialChart lecturas={lecturas} />
              {lecturas.length > 0 && (
                <div className="mb-6 mt-3 flex flex-wrap gap-4 text-xs text-muted-foreground">
                  {LEYENDA.map((l) => (
                    <span key={l.label} className="flex items-center gap-1.5">
                      <span className="h-2.5 w-2.5 rounded-full" style={{ background: l.color }} />
                      {l.label}
                    </span>
                  ))}
                  <span className="flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full border-2 border-info" />
                    Usado en facturación
                  </span>
                </div>
              )}

              <p className="mb-2 text-xs font-bold uppercase tracking-wide text-muted-foreground">
                Lecturas — últimos 24 meses
              </p>
              <TablaLecturas lecturas={lecturas} />
              <p className="mt-3 flex flex-wrap justify-between gap-2 text-xs text-muted-foreground">
                <span>
                  {lecturas.length} lecturas · {lecturas.filter((l) => l.es_fc).length} períodos FC · últimos 24 meses
                </span>
                <span>Solo lectura — para editar P/L usá el panel de candidatos (👁)</span>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

const DIVISORIA: { campo: keyof HistorialLectura; texto: string; clase: string }[] = [
  { campo: "cambio_empresa_vs_anterior", texto: "cambio de empresa", clase: "border-t-2 border-destructive text-destructive" },
  { campo: "cambio_sucursal_vs_anterior", texto: "cambio de sucursal", clase: "border-t-2 border-brand-orange text-brand-orange" },
  { campo: "cambio_anexo_vs_anterior", texto: "cambio de anexo", clase: "border-t border-dashed border-warning text-warning" },
];

/** Línea que marca dónde el equipo cambió de ubicación (empresa > sucursal > anexo). */
function Divisoria({ lectura }: { lectura: HistorialLectura }) {
  const d = DIVISORIA.find((x) => lectura[x.campo] === true);
  if (!d) return null;
  return (
    <tr aria-hidden>
      <td colSpan={7} className={cn("px-3 pb-0.5 pt-0 text-[10px] font-semibold", d.clase)}>
        {d.texto}
      </td>
    </tr>
  );
}

/** `ValidacionCssClass`: ok en verde, PF = 0 en amarillo, el resto informativo. */
function tonoValidacion(l: HistorialLectura): string {
  const t = l.id_tipo_toma;
  if (t === 4) return l.para_facturar ? "text-success" : "text-warning";
  if (t === 8 || t === 13) return l.es_fc ? "text-success" : "text-info";
  return esTipoReal(t) ? "text-success" : "text-info";
}

function FilaLectura({ l }: { l: HistorialLectura }) {
  const color = colorPunto(l.id_tipo_toma);
  return (
    <tr className={l.es_fc ? "bg-info/5" : ""}>
      <td className="px-3 py-1.5">
        <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: color }} />
      </td>
      <td className="px-3 py-1.5 tabular-nums">{fechaLarga(l.fecha)}</td>
      <td className="px-3 py-1.5">
        <span className="font-semibold" style={{ color }}>
          T{l.id_tipo_toma} · {l.tipo_toma_desc}
        </span>
        {l.es_fc && <span className="ml-1.5 rounded-full bg-info/20 px-1.5 text-[10px] font-bold text-info">FC</span>}
      </td>
      <td className="px-3 py-1.5 text-right font-semibold tabular-nums">{n0(l.valor)}</td>
      <td className="px-3 py-1.5 text-right tabular-nums">
        {l.delta === null ? <span className="text-muted-foreground">—</span> : `${l.delta >= 0 ? "+" : ""}${n0(l.delta)}`}
      </td>
      <td className="px-3 py-1.5">
        {l.es_fc && l.fc_periodo_facturacion ? l.fc_periodo_facturacion : <span className="text-muted-foreground">—</span>}
      </td>
      <td className={cn("px-3 py-1.5", tonoValidacion(l))}>{validacionHistorial(l)}</td>
    </tr>
  );
}

function TablaLecturas({ lecturas }: { lecturas: HistorialLectura[] }) {
  if (lecturas.length === 0) return <p className="text-sm text-muted-foreground">Sin lecturas registradas.</p>;
  return (
    <div className="overflow-x-auto rounded-[8px] border border-border">
      <table className="w-full min-w-[680px] text-left text-xs">
        <thead className="bg-muted/40 text-[10px] font-bold uppercase tracking-wide text-muted-foreground">
          <tr>
            <th className="w-4 px-3 py-2" />
            <th className="px-3 py-2">Fecha</th>
            <th className="px-3 py-2">Tipo de toma</th>
            <th className="px-3 py-2 text-right">Valor</th>
            <th className="px-3 py-2 text-right">Δ impr.</th>
            <th className="px-3 py-2">Período de fact.</th>
            <th className="px-3 py-2">Validación</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {lecturas.map((l, i) => (
            <Fragment key={i}>
              <FilaLectura l={l} />
              <Divisoria lectura={l} />
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
