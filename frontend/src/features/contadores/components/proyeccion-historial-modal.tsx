"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { proyeccionApi } from "../api/proyeccion-api";
import type { FilaProyeccion, HistorialLectura } from "../types/proyeccion";
import { HistorialChart } from "./proyeccion-historial-chart";

/** Línea de tiempo de un equipo — paridad con `DrillDownModal` legacy. Solo
 * lectura: para editar Partida/Llegada se usa el panel de candidatos (ícono
 * de ojo). Identidad del equipo viene de la fila que abrió el modal — ya la
 * tiene la tabla, evita duplicar la consulta de metadata contra Siges. */

const numberFormat = new Intl.NumberFormat("es-AR");

function formatFecha(iso: string): string {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
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
      .catch(() => setError("No se pudo cargar el historial."));
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
                {fila.tecnologia === "MONO" ? "Mono" : "Color"}
              </span>
              <span className="text-[10px] font-bold uppercase text-muted-foreground">Cl. {fila.clase}</span>
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
          {error && <p className="text-sm text-destructive">{error}</p>}
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
              <p className="mt-3 text-xs text-muted-foreground">
                {lecturas.length} lectura{lecturas.length === 1 ? "" : "s"} · últimos 24 meses · Solo lectura — para
                editar P/L usá el panel de candidatos.
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function validacion(l: HistorialLectura): string {
  if (l.id_tipo_toma === 14 || l.id_tipo_toma === 19) return "—";
  if (l.id_tipo_toma === 4) return l.para_facturar ? "T4 facturado" : "⚠ PF = 0";
  if (l.id_tipo_toma === 16) return "Reinicio de contador";
  if (l.id_tipo_toma === 8 || l.id_tipo_toma === 13) {
    if (l.es_fc) return "✓ Válida";
    if (l.es_cambio_empresa) return "Cambio de empresa";
    if (l.es_cambio_anexo) return "Cambio de anexo";
    if (l.es_ingreso) return "Ingreso del equipo";
    if (l.es_egreso) return "Egreso del equipo";
    return l.id_tipo_toma === 8 ? "Apertura" : "Cierre";
  }
  return "✓ Válida";
}

function TablaLecturas({ lecturas }: { lecturas: HistorialLectura[] }) {
  if (lecturas.length === 0) return <p className="text-sm text-muted-foreground">Sin lecturas registradas.</p>;
  return (
    <div className="overflow-x-auto rounded-[8px] border border-border">
      <table className="w-full min-w-[640px] text-left text-xs">
        <thead className="bg-muted/40 text-[10px] font-bold uppercase tracking-wide text-muted-foreground">
          <tr>
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
            <tr key={i} className={l.cambio_empresa_vs_anterior || l.cambio_sucursal_vs_anterior ? "border-t-2 border-t-brand-orange/40" : ""}>
              <td className="px-3 py-1.5 tabular-nums">{formatFecha(l.fecha)}</td>
              <td className="px-3 py-1.5">
                T{l.id_tipo_toma} · {l.tipo_toma_desc}
              </td>
              <td className="px-3 py-1.5 text-right tabular-nums">{numberFormat.format(l.valor)}</td>
              <td className="px-3 py-1.5 text-right tabular-nums text-muted-foreground">
                {l.delta === null ? "—" : `${l.delta >= 0 ? "+" : ""}${numberFormat.format(l.delta)}`}
              </td>
              <td className="px-3 py-1.5">{l.fc_periodo_facturacion ?? "—"}</td>
              <td className="px-3 py-1.5">{validacion(l)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
