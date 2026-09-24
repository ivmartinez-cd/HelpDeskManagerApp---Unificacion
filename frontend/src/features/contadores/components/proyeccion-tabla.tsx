"use client";

import { BarChart3, Eye } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import type { SortState } from "@/shared/hooks/use-table-sort";
import type { FilaProyeccion } from "../types/proyeccion";
import {
  AFacturarCell,
  ImpresionesCell,
  MesesCell,
  ModeloCell,
  SemaforoCell,
  UbicacionCell,
  UltimoFacturadoCell,
} from "./proyeccion-celdas";
import { n0 } from "./proyeccion-formato";
import type { GrupoEquipo, ProyeccionSortKey } from "./proyeccion-orden";
import { ProyeccionSparkline } from "./proyeccion-sparkline";

export function claveFila(fila: FilaProyeccion): string {
  return `${fila.id_maquina}-${fila.clase}`;
}

/** Agrupa por máquina conservando el orden de llegada y ordena las clases. */
export function agruparPorEquipo(filas: FilaProyeccion[]): GrupoEquipo[] {
  const porId = new Map<number, FilaProyeccion[]>();
  for (const fila of filas) porId.set(fila.id_maquina, [...(porId.get(fila.id_maquina) ?? []), fila]);
  return Array.from(porId.values()).map((lista) => ({
    filas: [...lista].sort((a, b) => Number(a.clase) - Number(b.clase)),
  }));
}

interface ProyeccionTablaProps {
  grupos: GrupoEquipo[];
  sort: SortState<ProyeccionSortKey>;
  onToggleSort: (key: ProyeccionSortKey) => void;
  activa: FilaProyeccion | null;
  onVerCandidatos: (fila: FilaProyeccion) => void;
  onVerHistorial: (fila: FilaProyeccion) => void;
  fechaObjetivo: string | null;
}

const TH = "px-3 py-2.5";

export function ProyeccionTabla(props: ProyeccionTablaProps) {
  const { grupos, sort, onToggleSort } = props;
  return (
    <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
      <table className="w-full min-w-[1180px] text-left text-sm">
        <thead>
          <tr className="border-b border-border font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            <SortableHeader column={{ key: "ubicacion", label: "Ubicación" }} sort={sort} onToggleSort={onToggleSort} thClassName={TH} />
            <SortableHeader column={{ key: "nro_serie", label: "Nro. serie" }} sort={sort} onToggleSort={onToggleSort} thClassName={TH} />
            <SortableHeader column={{ key: "modelo", label: "Modelo" }} sort={sort} onToggleSort={onToggleSort} thClassName={TH} />
            <SortableHeader column={{ key: "meses", label: "Meses sin real" }} sort={sort} onToggleSort={onToggleSort} thClassName={cn(TH, "text-center")} />
            <SortableHeader column={{ key: "historico", label: "12 meses" }} sort={sort} onToggleSort={onToggleSort} thClassName={cn(TH, "text-center")} />
            <SortableHeader column={{ key: "prom6", label: "Prom 6m" }} sort={sort} onToggleSort={onToggleSort} thClassName={cn(TH, "text-right")} />
            <SortableHeader column={{ key: "clases", label: "Cl." }} sort={sort} onToggleSort={onToggleSort} thClassName={cn(TH, "text-center")} />
            <SortableHeader column={{ key: "ultimo_facturado", label: "Últ. facturado" }} sort={sort} onToggleSort={onToggleSort} thClassName={cn(TH, "text-right")} />
            <SortableHeader column={{ key: "a_facturar", label: "A facturar" }} sort={sort} onToggleSort={onToggleSort} thClassName={cn(TH, "text-right")} />
            <SortableHeader column={{ key: "impresiones", label: "Impresiones" }} sort={sort} onToggleSort={onToggleSort} thClassName={cn(TH, "text-right")} />
            <th className={cn(TH, "text-center")}>Acc.</th>
            <SortableHeader column={{ key: "semaforo", label: "Conf." }} sort={sort} onToggleSort={onToggleSort} thClassName={cn(TH, "text-center")} />
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {grupos.map((g) => g.filas.map((fila, i) => <FilaTabla key={claveFila(fila)} {...props} grupo={g} fila={fila} primera={i === 0} />))}
        </tbody>
      </table>
    </div>
  );
}

interface FilaTablaProps extends ProyeccionTablaProps {
  grupo: GrupoEquipo;
  fila: FilaProyeccion;
  primera: boolean;
}

/** "sin historia propia": la fila principal sale de la cascada T19 por modelo. */
function esT19(fila: FilaProyeccion): boolean {
  return ["Parque_Cliente_Modelo", "Parque_Grupo_Modelo", "Parque_Global_Modelo"].includes(fila.fuente);
}

function FilaTabla({ grupo, fila, primera, activa, fechaObjetivo, onVerCandidatos, onVerHistorial }: FilaTablaProps) {
  const principal = grupo.filas[0];
  const span = grupo.filas.length;
  const equipoActivo = activa?.id_maquina === fila.id_maquina;
  const botonActivo = equipoActivo && activa?.clase === fila.clase;
  return (
    <tr className={cn("hover:bg-muted/30", equipoActivo && "bg-brand-orange/5", primera && "border-t-2 border-t-border")}>
      {primera && (
        <>
          <td className="px-3 py-3 align-top" rowSpan={span}>
            <UbicacionCell fila={principal} />
          </td>
          <td className="px-3 py-3 align-top font-mono text-xs" rowSpan={span}>
            {principal.nro_serie}
            <div className="mt-1 flex flex-wrap gap-1 font-body">
              {esT19(principal) && <Badge className="border-destructive bg-destructive/10 text-destructive">sin historia propia</Badge>}
              {principal.editado_por_operador && (
                <Badge className="border-warning bg-warning/10 text-warning" title="P/L modificado por operador">editado</Badge>
              )}
            </div>
          </td>
          <td className="max-w-[200px] px-3 py-3 align-top" rowSpan={span}>
            <ModeloCell fila={principal} />
          </td>
          <td className="px-3 py-3 text-center align-top" rowSpan={span}>
            <MesesCell fila={principal} />
          </td>
        </>
      )}
      <td className="px-3 py-3">
        <ProyeccionSparkline historico12={fila.historico_12} impresiones={fila.impresiones} prom6={fila.prom_6_facturados} />
      </td>
      <td className="px-3 py-3 text-right tabular-nums">{n0(fila.prom_6_facturados)}</td>
      <td className="px-3 py-3 text-center">{fila.clase}</td>
      <td className="px-3 py-3 text-right leading-tight">
        <UltimoFacturadoCell fila={fila} />
      </td>
      <td className="px-3 py-3 text-right leading-tight">
        <AFacturarCell fila={fila} fechaObjetivo={fechaObjetivo} />
      </td>
      <td className="px-3 py-3 text-right">
        <ImpresionesCell fila={fila} />
      </td>
      <td className="px-3 py-3">
        <div className="flex justify-center gap-1.5">
          <IconButton titulo={`Ver candidatos (Cl. ${fila.clase})`} activo={botonActivo} onClick={() => onVerCandidatos(fila)}>
            <Eye className="h-4 w-4" />
          </IconButton>
          <IconButton titulo={`Historial del contador (Cl. ${fila.clase})`} onClick={() => onVerHistorial(fila)}>
            <BarChart3 className="h-4 w-4" />
          </IconButton>
        </div>
      </td>
      <td className="px-3 py-3 text-center">
        <SemaforoCell fila={fila} />
      </td>
    </tr>
  );
}

function Badge({ className, title, children }: { className: string; title?: string; children: React.ReactNode }) {
  return (
    <span title={title} className={cn("rounded-full border px-1.5 py-px text-[10px] font-bold", className)}>
      {children}
    </span>
  );
}

function IconButton({ titulo, activo, onClick, children }: { titulo: string; activo?: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={titulo}
      className={cn(
        "rounded-[8px] border border-border bg-muted p-1.5 text-muted-foreground hover:text-foreground",
        activo && "border-brand-orange bg-brand-orange/10 text-brand-orange",
      )}
    >
      {children}
    </button>
  );
}
