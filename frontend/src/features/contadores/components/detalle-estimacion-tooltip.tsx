"use client";

import { Tooltip } from "@/shared/components/ui/tooltip";
import { cn } from "@/shared/utils/cn";
import type { FilaProyeccion, MetodoEstimacion } from "../types/proyeccion";
import { n0, n2 } from "./proyeccion-formato";

/** Tooltip "Detalle de estimación" de la celda Impresiones — puerto de
 * `EstimacionTooltip.razor` (v1.7). Se muestra solo si la fila tiene un
 * método de estimación (no "NoAplica"), no es "Sin_Estimar" y tiene
 * impresiones (`HasTooltip` de la grilla). */

const FUENTE_LABEL: Record<string, string> = {
  Historia_Propia: "Entre lecturas reales del propio equipo",
  Parque_Cliente_Tec: "Parque del cliente · misma tecnología",
  Parque_Cliente_Modelo: "Parque del cliente · mismo modelo",
  Parque_Grupo_Modelo: "Parque del grupo económico · mismo modelo",
  Parque_Global_Modelo: "Parque global · mismo modelo",
  T4_ST: "Valor T4 ST como Llegada",
  Backup_SinST: "Backup sin movimiento",
  EnTransito: "En tránsito · sin movimiento",
};

const METODO_LABEL: Record<MetodoEstimacion, string> = {
  NoAplica: "—",
  MedianaTruncadaP80: "Mediana truncada P80",
  MedianaCruda: "Mediana cruda (muestra chica)",
  EntreReales: "Regla de tres entre P y L",
  ContadorAnterior: "Repetir contador anterior",
  T4ST_Valor: "T4 ST como Llegada",
  T4ST_Proyectado: "T4 ST proyectado a fecha objetivo",
};

export function tieneDetalleEstimacion(fila: FilaProyeccion): boolean {
  return fila.metodo !== "NoAplica" && fila.fuente !== "Sin_Estimar" && fila.impresiones !== null;
}

function Fila({ k, v, strong, muted }: { k: string; v: React.ReactNode; strong?: boolean; muted?: boolean }) {
  return (
    <tr>
      <td className={cn("py-0.5 pr-3 text-muted-foreground", muted && "opacity-80")}>{k}</td>
      <td className={cn("py-0.5 text-right tabular-nums", strong && "font-bold text-foreground", muted && "text-muted-foreground")}>
        {v}
      </td>
    </tr>
  );
}

function FilasParque({ fila }: { fila: FilaProyeccion }) {
  const d = fila.detalle_parque;
  if (!d || d.n_equipos <= 0) return null;
  const truncada = fila.metodo === "MedianaTruncadaP80";
  return (
    <>
      <Fila
        k="Equipos del parque"
        v={
          <>
            {d.n_equipos}
            {d.n_descartados > 0 && <span className="text-muted-foreground"> ({d.n_descartados} descartados por &gt; P80)</span>}
          </>
        }
      />
      <Fila k={truncada ? "Mediana truncada" : "Mediana cruda"} v={`${n0(fila.impresiones)} imp`} strong />
      {truncada && d.mediana_cruda !== null && <Fila k="Mediana cruda (ref)" v={n0(d.mediana_cruda)} muted />}
      {d.media_cruda !== null && <Fila k="Media cruda (ref)" v={n0(d.media_cruda)} muted />}
    </>
  );
}

function FilasPar({ fila }: { fila: FilaProyeccion }) {
  if (fila.dias_par_pl === null || fila.dias_par_pl <= 0) return null;
  return (
    <>
      <Fila k="Días P → L" v={`${fila.dias_par_pl} d`} />
      <Fila k="Promedio diario" v={`${n2(fila.tasa_diaria)}/día`} />
      {/* El legacy antepone "+" siempre (también a una extrapolación negativa). */}
      <Fila k="Extrapolado" v={`+${fila.dias_proyectados ?? ""} d hasta fecha obj.`} />
      <Fila k="Impresiones estimadas" v={`${n0(fila.impresiones)} imp`} strong />
    </>
  );
}

function FilaSimple({ fila }: { fila: FilaProyeccion }) {
  if (fila.detalle_parque !== null || fila.dias_par_pl !== null) return null;
  return <Fila k="Impresiones" v={`${n0(fila.impresiones)} imp`} strong />;
}

interface DetalleEstimacionTooltipProps {
  fila: FilaProyeccion;
  className?: string;
  children: React.ReactNode;
}

export function DetalleEstimacionTooltip({ fila, className, children }: DetalleEstimacionTooltipProps) {
  const contenido = (
    <div className="w-64 font-body">
      <p className="text-xs font-bold text-foreground">Detalle de estimación</p>
      <p className="mb-2 text-[11px] text-muted-foreground">
        {fila.nro_serie} · {fila.clase === "10" ? "Mono" : "Color"}
      </p>
      <table className="w-full text-xs">
        <tbody>
          <Fila k="Estrategia" v={FUENTE_LABEL[fila.fuente] ?? fila.fuente} />
          <Fila k="Método" v={METODO_LABEL[fila.metodo]} />
          <FilasParque fila={fila} />
          <FilasPar fila={fila} />
          <FilaSimple fila={fila} />
        </tbody>
      </table>
      {fila.etiqueta_nivel?.trim() && (
        <p className="mt-2 border-t border-border pt-1.5 text-[11px] text-muted-foreground">{fila.etiqueta_nivel}</p>
      )}
    </div>
  );
  return (
    <Tooltip content={contenido} placement="left" className={className}>
      {children}
    </Tooltip>
  );
}
