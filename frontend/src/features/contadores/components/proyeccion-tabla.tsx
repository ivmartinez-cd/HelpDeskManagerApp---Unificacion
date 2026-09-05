"use client";

import { Eye } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import { BrandBadge } from "@/shared/components/ui/brand-form";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import type { SortState } from "@/shared/hooks/use-table-sort";
import type { FilaProyeccion, Semaforo } from "../types/proyeccion";
import { ProyeccionSparkline } from "./proyeccion-sparkline";

export type ProyeccionSortKey = "ubicacion" | "nro_serie" | "modelo" | "impresiones";

const SEMAFORO_DOT: Record<Semaforo, string> = {
  VERDE: "bg-success",
  AMARILLO: "bg-warning",
  NARANJA: "bg-brand-orange",
  ROJO: "bg-destructive",
};

const SEMAFORO_LABEL: Record<Semaforo, string> = {
  VERDE: "Verde — real, o estimado de alta confianza",
  AMARILLO: "Amarillo — requiere confirmación (T4 sin revisar, receso, backup/tránsito)",
  NARANJA: "Naranja — desvío del propio equipo",
  ROJO: "Rojo — parque (sin historia), pendiente o salto imposible",
};

const numberFormat = new Intl.NumberFormat("es-AR");

function formatFecha(iso: string): string {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

function ImpresionesCell({ fila }: { fila: FilaProyeccion }) {
  if (fila.impresiones === null) return <span className="text-muted-foreground">—</span>;
  const signo = fila.impresiones >= 0 ? "+" : "";
  const tono =
    fila.coloreo === "AZUL"
      ? "text-info"
      : fila.coloreo === "NARANJA"
        ? "text-brand-orange"
        : "text-foreground";
  return (
    <span
      className={cn(
        "font-bold tabular-nums",
        tono,
        fila.borde_salto_imposible && "rounded-[8px] border-2 border-dashed border-destructive px-2 py-0.5",
      )}
      title={fila.borde_salto_imposible ? "Salto imposible: supera la capacidad física del equipo" : undefined}
    >
      {signo}
      {numberFormat.format(fila.impresiones)}
    </span>
  );
}

function EstimCell({ fila }: { fila: FilaProyeccion }) {
  if (fila.estim_propuesto === null) return <span className="text-muted-foreground">—</span>;
  const t4SinRevisar = fila.tipo_toma === 4;
  return (
    <div className="leading-tight">
      <span className="font-semibold tabular-nums">{numberFormat.format(fila.estim_propuesto)}</span>
      {fila.tipo_toma !== null && (
        <span className={cn("ml-1 text-[10px] font-bold", t4SinRevisar ? "text-warning" : "text-muted-foreground")}>
          T{fila.tipo_toma}
          {t4SinRevisar && " ⚠"}
        </span>
      )}
    </div>
  );
}

interface FilaAgrupada {
  claves: FilaProyeccion[];
}

function agruparPorEquipo(filas: FilaProyeccion[]): FilaAgrupada[] {
  const porId = new Map<number, FilaProyeccion[]>();
  for (const fila of filas) {
    const lista = porId.get(fila.id_maquina) ?? [];
    lista.push(fila);
    porId.set(fila.id_maquina, lista);
  }
  return Array.from(porId.values()).map((claves) => ({ claves }));
}

interface ProyeccionTablaProps {
  filas: FilaProyeccion[];
  sort: SortState<ProyeccionSortKey>;
  onToggleSort: (key: ProyeccionSortKey) => void;
  onVerCandidatos: (fila: FilaProyeccion) => void;
}

export function ProyeccionTabla({ filas, sort, onToggleSort, onVerCandidatos }: ProyeccionTablaProps) {
  const grupos = agruparPorEquipo(filas);

  return (
    <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
      <table className="w-full min-w-[1180px] text-left text-sm">
        <thead>
          <tr className="border-b border-border font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            <SortableHeader column={{ key: "ubicacion", label: "Ubicación" }} sort={sort} onToggleSort={onToggleSort} thClassName="px-4 py-2.5" />
            <SortableHeader column={{ key: "nro_serie", label: "Nro. serie" }} sort={sort} onToggleSort={onToggleSort} thClassName="px-4 py-2.5" />
            <SortableHeader column={{ key: "modelo", label: "Modelo" }} sort={sort} onToggleSort={onToggleSort} thClassName="px-4 py-2.5" />
            <th className="px-4 py-2.5">Meses sin real</th>
            <th className="px-4 py-2.5">12 meses</th>
            <th className="px-4 py-2.5 text-right">Prom 6m</th>
            <th className="px-4 py-2.5">Cl.</th>
            <th className="px-4 py-2.5 text-right">Últ. facturado</th>
            <th className="px-4 py-2.5 text-right">Estim. propuesto</th>
            <SortableHeader column={{ key: "impresiones", label: "Impresiones" }} sort={sort} onToggleSort={onToggleSort} thClassName="px-4 py-2.5 text-right" />
            <th className="px-4 py-2.5">Conf.</th>
            <th className="px-4 py-2.5" />
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {grupos.map(({ claves }) =>
            claves.map((fila, i) => (
              <tr key={`${fila.id_maquina}-${fila.clase}`} className="hover:bg-muted/30">
                {i === 0 && (
                  <>
                    <td className="px-4 py-3" rowSpan={claves.length}>
                      <p className="font-semibold text-foreground">{fila.empresa}</p>
                      <p className="text-xs text-muted-foreground">{fila.sucursal}</p>
                      <p className="text-xs text-info">Sector: {fila.sector}</p>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs" rowSpan={claves.length}>
                      {fila.nro_serie}
                      {fila.estado_maquina !== "NORMAL" && (
                        <BrandBadge variant="warning">
                          {fila.estado_maquina === "BACKUP" ? "Backup" : "En tránsito"}
                        </BrandBadge>
                      )}
                    </td>
                    <td className="max-w-[200px] px-4 py-3" rowSpan={claves.length}>
                      <p className="truncate font-semibold" title={fila.modelo}>{fila.modelo}</p>
                      <p className="text-xs uppercase text-muted-foreground">{fila.tecnologia}</p>
                    </td>
                    <td className="px-4 py-3" rowSpan={claves.length}>
                      {fila.meses_sin_real === null ? (
                        "—"
                      ) : (
                        <span className={fila.meses_sin_real > 12 || (fila.tecnologia === "COLOR" && fila.meses_sin_real > 6) ? "font-bold text-destructive" : ""}>
                          {fila.meses_sin_real}
                        </span>
                      )}
                    </td>
                  </>
                )}
                <td className="px-4 py-3">
                  <ProyeccionSparkline historico12={fila.historico_12} />
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  {fila.prom_6_facturados !== null ? numberFormat.format(fila.prom_6_facturados) : "—"}
                </td>
                <td className="px-4 py-3">
                  {fila.clase}
                  {fila.es_clase_sintetica && (
                    <span
                      title="Clase sintética: el equipo la tiene declarada en su modo de operación, pero nadie cargó todavía su lectura para este proceso"
                      className="ml-1 text-[10px] font-bold text-muted-foreground"
                    >
                      *
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-right leading-tight">
                  <p className="tabular-nums">{numberFormat.format(fila.ultimo_facturado_valor)}</p>
                  <p className="text-xs text-muted-foreground">{formatFecha(fila.ultimo_facturado_fecha)}</p>
                </td>
                <td className="px-4 py-3 text-right">
                  <EstimCell fila={fila} />
                </td>
                <td className="px-4 py-3 text-right">
                  <ImpresionesCell fila={fila} />
                </td>
                {i === 0 && (
                  <>
                    <td className="px-4 py-3" rowSpan={claves.length}>
                      <span
                        aria-label={SEMAFORO_LABEL[fila.semaforo]}
                        title={SEMAFORO_LABEL[fila.semaforo]}
                        className={cn("inline-block h-2.5 w-2.5 rounded-full", SEMAFORO_DOT[fila.semaforo])}
                      />
                    </td>
                    <td className="px-4 py-3" rowSpan={claves.length}>
                      <button
                        type="button"
                        onClick={() => onVerCandidatos(fila)}
                        title="Ver candidatos"
                        className="rounded-[8px] border border-border bg-muted p-1.5 text-muted-foreground hover:text-foreground"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    </td>
                  </>
                )}
              </tr>
            )),
          )}
        </tbody>
      </table>
    </div>
  );
}
