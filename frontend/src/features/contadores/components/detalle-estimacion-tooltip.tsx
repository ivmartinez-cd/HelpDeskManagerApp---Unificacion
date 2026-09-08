"use client";

import { Info } from "lucide-react";
import { Tooltip } from "@/shared/components/ui/tooltip";
import { cn } from "@/shared/utils/cn";
import type { FilaProyeccion } from "../types/proyeccion";

/** Tooltip rico con la composición de la estimación (paridad con
 * `EstimacionTooltip.razor` del legacy) — se muestra al lado de la celda
 * Impresiones cuando hay una decisión estructurada que vale la pena ver
 * (parque, P/L, T4). No se renderiza para real / pendiente / sin estimar. */

const numberFormat = new Intl.NumberFormat("es-AR");
const decimalFormat = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 2 });

function N(v: number | null): string {
  return v === null ? "—" : numberFormat.format(v);
}

const FUENTE_LABEL: Record<string, string> = {
  Historia_Propia: "Entre lecturas reales del propio equipo",
  Parque_Cliente_Tec: "Parque del cliente · misma tecnología",
  Parque_Cliente_Modelo: "Parque del cliente · mismo modelo",
  Parque_Grupo_Modelo: "Parque del grupo económico · mismo modelo",
  Parque_Global_Modelo: "Parque global · mismo modelo",
  T4_ST: "Valor T4 ST como Llegada",
  Backup_SinST: "Backup sin movimiento",
  Backup_ConST: "Backup con Servicio Técnico",
  EnTransito: "En tránsito · sin movimiento",
};

const METODO_LABEL_POR_DETALLE: Record<string, string> = {
  "Entre dos reales": "Regla de tres entre P y L",
  "Partida/Llegada elegidas a mano": "P/L manual",
  "T4ST valor": "T4 ST tal cual",
  "T4ST proyectado": "T4 ST proyectado a fecha objetivo",
  "Sin movimiento": "Repetir contador anterior",
};

function metodoLabel(fila: FilaProyeccion): string {
  if (fila.detalle_parque) {
    return fila.detalle_parque.es_mediana_truncada
      ? "Mediana truncada P80"
      : "Mediana cruda (muestra chica)";
  }
  return METODO_LABEL_POR_DETALLE[fila.metodo_detalle] ?? "—";
}

/** No hay nada estructurado que mostrar: real, sin estimar, pendiente, o sin
 * ninguna de las 3 formas de decisión (parque / P-L / caso simple). */
export function tieneDetalleEstimacion(fila: FilaProyeccion): boolean {
  if (fila.es_real || fila.impresiones === null) return false;
  return fila.fuente !== "Sin_Estimar" && fila.fuente !== "Pendiente";
}

function Fila({ k, v, strong, muted }: { k: string; v: React.ReactNode; strong?: boolean; muted?: boolean }) {
  return (
    <tr>
      <td className="pr-3 py-0.5 text-muted-foreground">{k}</td>
      <td
        className={cn(
          "py-0.5 text-right tabular-nums",
          strong && "font-bold text-foreground",
          muted && "text-muted-foreground",
        )}
      >
        {v}
      </td>
    </tr>
  );
}

function FilasParque({ fila }: { fila: FilaProyeccion }) {
  const d = fila.detalle_parque;
  if (!d) return null;
  return (
    <>
      <Fila
        k="Equipos del parque"
        v={
          <>
            {d.n_equipos}
            {d.n_descartados > 0 && (
              <span className="text-muted-foreground"> ({d.n_descartados} descartados por &gt; P80)</span>
            )}
          </>
        }
      />
      <Fila k={d.es_mediana_truncada ? "Mediana truncada" : "Mediana cruda"} v={`${N(fila.impresiones)} imp`} strong />
      {d.es_mediana_truncada && d.mediana_cruda !== null && (
        <Fila k="Mediana cruda (ref)" v={N(d.mediana_cruda)} muted />
      )}
      {d.media_cruda !== null && <Fila k="Media cruda (ref)" v={N(d.media_cruda)} muted />}
    </>
  );
}

function FilasEntreReales({ fila }: { fila: FilaProyeccion }) {
  if (fila.detalle_parque || fila.dias_par_pl === null) return null;
  return (
    <>
      <Fila k="Días P → L" v={`${fila.dias_par_pl} d`} />
      <Fila k="Promedio diario" v={`${fila.tasa_diaria !== null ? decimalFormat.format(fila.tasa_diaria) : "—"}/día`} />
      <Fila k="Extrapolado" v={`+${fila.dias_proyectados ?? 0} d hasta fecha obj.`} />
      <Fila k="Impresiones estimadas" v={`${N(fila.impresiones)} imp`} strong />
    </>
  );
}

function FilasSimple({ fila }: { fila: FilaProyeccion }) {
  if (fila.detalle_parque || fila.dias_par_pl !== null) return null;
  return <Fila k="Impresiones" v={`${N(fila.impresiones)} imp`} strong />;
}

export function DetalleEstimacionTooltip({ fila, children }: { fila: FilaProyeccion; children: React.ReactNode }) {
  const contenido = (
    <div className="w-64 font-body">
      <p className="mb-1 text-xs font-bold text-foreground">Detalle de estimación</p>
      <p className="mb-2 text-[11px] text-muted-foreground">
        {fila.nro_serie} · {fila.tecnologia === "MONO" ? "Mono" : "Color"}
      </p>
      <table className="w-full text-xs">
        <tbody>
          <Fila k="Estrategia" v={FUENTE_LABEL[fila.fuente] ?? fila.fuente} />
          <Fila k="Método" v={metodoLabel(fila)} />
          <FilasParque fila={fila} />
          <FilasEntreReales fila={fila} />
          <FilasSimple fila={fila} />
        </tbody>
      </table>
    </div>
  );
  return (
    <Tooltip content={contenido} placement="left">
      {children}
    </Tooltip>
  );
}

export function DetalleEstimacionIcono({ fila }: { fila: FilaProyeccion }) {
  if (!tieneDetalleEstimacion(fila)) return null;
  return (
    <DetalleEstimacionTooltip fila={fila}>
      <Info className="h-3.5 w-3.5 cursor-help text-muted-foreground" aria-label="Ver detalle de la estimación" />
    </DetalleEstimacionTooltip>
  );
}
