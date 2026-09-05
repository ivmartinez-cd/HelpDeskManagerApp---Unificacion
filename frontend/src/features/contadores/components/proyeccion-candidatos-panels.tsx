"use client";

import { cn } from "@/shared/utils/cn";
import { BrandButton } from "@/shared/components/ui/brand-form";
import type { CandidatoLectura, CandidatosEquipo, MetodoForzado } from "../types/proyeccion";

export function formatFecha(iso: string): string {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

export const numberFormat = new Intl.NumberFormat("es-AR");

export interface Seleccion {
  partida: CandidatoLectura | null;
  llegada: CandidatoLectura | null;
}

export interface Calculo {
  estim: number | null;
  impresiones: number | null;
  tipoToma: number | null;
  fuente: string;
  metodoDetalle: string;
}

interface ProyeccionLecturasTablaProps {
  datos: CandidatosEquipo | null;
  error: string | null;
  seleccion: Seleccion;
  puedeGestionar: boolean;
  onElegir: (rol: "partida" | "llegada", lectura: CandidatoLectura) => void;
}

export function ProyeccionLecturasTabla({
  datos,
  error,
  seleccion,
  puedeGestionar,
  onElegir,
}: ProyeccionLecturasTablaProps) {
  if (error) return <p className="text-sm text-warning">{error}</p>;
  if (!datos) return <p className="text-sm text-muted-foreground">Cargando…</p>;

  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="text-left text-[10px] uppercase text-muted-foreground">
          <th className="py-1.5">Fecha</th>
          <th className="py-1.5">Tipo</th>
          <th className="py-1.5 text-right">Valor</th>
          <th className="py-1.5">Valid.</th>
          <th className="py-1.5">P</th>
          <th className="py-1.5">L</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-border">
        {datos.lecturas.map((lectura) => (
          <tr key={`${lectura.fecha}-${lectura.tipo_toma}-${lectura.valor}`}>
            <td className="py-2">{formatFecha(lectura.fecha)}</td>
            <td className="py-2">T{lectura.tipo_toma}</td>
            <td className="py-2 text-right tabular-nums">{numberFormat.format(lectura.valor)}</td>
            <td className={cn("py-2", lectura.valido ? "text-success" : "text-warning")}>
              {lectura.valido ? "✓ ok" : lectura.motivo_invalidez}
            </td>
            <td className="py-2">
              <button
                disabled={!puedeGestionar}
                onClick={() => onElegir("partida", lectura)}
                className={cn(
                  "h-6 w-6 rounded-[6px] border border-border bg-muted text-[10px] font-extrabold disabled:opacity-40",
                  seleccion.partida === lectura && "border-success bg-success text-background",
                )}
              >
                P
              </button>
            </td>
            <td className="py-2">
              <button
                disabled={!puedeGestionar}
                onClick={() => onElegir("llegada", lectura)}
                className={cn(
                  "h-6 w-6 rounded-[6px] border border-border bg-muted text-[10px] font-extrabold disabled:opacity-40",
                  seleccion.llegada === lectura && "border-info bg-info text-background",
                )}
              >
                L
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

interface ProyeccionCalculoPanelProps {
  seleccion: Seleccion;
  calculoVisible: Calculo | null;
  forzado: Calculo | null;
  puedeGestionar: boolean;
  forzando: MetodoForzado | null;
  onForzar: (metodo: MetodoForzado) => void;
}

export function ProyeccionCalculoPanel({
  seleccion,
  calculoVisible,
  forzado,
  puedeGestionar,
  forzando,
  onForzar,
}: ProyeccionCalculoPanelProps) {
  const estim =
    calculoVisible?.estim !== null && calculoVisible?.estim !== undefined
      ? calculoVisible.estim
      : forzado?.estim !== null && forzado?.estim !== undefined
        ? forzado.estim
        : null;
  const impresiones =
    calculoVisible?.impresiones !== null && calculoVisible?.impresiones !== undefined
      ? calculoVisible.impresiones
      : forzado?.impresiones !== null && forzado?.impresiones !== undefined
        ? forzado.impresiones
        : null;

  return (
    <>
      <p className="mb-2 mt-6 text-[10.5px] font-bold uppercase tracking-wide text-muted-foreground">
        Cálculo
      </p>
      <dl className="grid grid-cols-2 gap-y-2 text-[12.5px]">
        <dt className="text-muted-foreground">P → L</dt>
        <dd className="text-right tabular-nums">
          {seleccion.partida ? formatFecha(seleccion.partida.fecha) : "—"} →{" "}
          {seleccion.llegada ? formatFecha(seleccion.llegada.fecha) : "—"}
        </dd>
        <dt className="text-muted-foreground">Estim. propuesto</dt>
        <dd className="text-right font-heading text-base font-extrabold text-brand-orange tabular-nums">
          {estim !== null && estim !== undefined ? numberFormat.format(estim) : "—"}
        </dd>
        <dt className="text-muted-foreground">Impresiones del período</dt>
        <dd className="text-right font-heading text-base font-extrabold text-brand-orange tabular-nums">
          {impresiones !== null && impresiones !== undefined ? numberFormat.format(impresiones) : "—"}
        </dd>
        {!calculoVisible && forzado && (
          <>
            <dt className="text-muted-foreground">Método forzado</dt>
            <dd className="text-right text-xs text-muted-foreground">{forzado.metodoDetalle}</dd>
          </>
        )}
      </dl>

      {puedeGestionar && (
        <div className="mt-3 flex gap-2">
          <BrandButton
            variant="outline"
            className="flex-1 text-xs"
            loading={forzando === "entre_reales"}
            disabled={forzando !== null}
            onClick={() => onForzar("entre_reales")}
          >
            Forzar entre reales
          </BrandButton>
          <BrandButton
            variant="outline"
            className="flex-1 text-xs"
            loading={forzando === "cascada_parque"}
            disabled={forzando !== null}
            onClick={() => onForzar("cascada_parque")}
          >
            Forzar cascada de parque
          </BrandButton>
        </div>
      )}
    </>
  );
}
