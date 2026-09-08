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
  diasParPl: number | null;
  tasaDiaria: number | null;
  diasProyectados: number | null;
}

const decimalFormat = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 2 });

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
    <div className="max-h-64 overflow-y-auto rounded-[8px] border border-border thin-scrollbar">
      <table className="w-full text-xs">
        <thead className="sticky top-0 bg-muted">
          <tr className="text-left text-[10px] uppercase text-muted-foreground">
            <th className="py-1.5 pl-2">Fecha</th>
            <th className="py-1.5">Tipo</th>
            <th className="py-1.5 text-right">Valor</th>
            <th className="py-1.5">Valid.</th>
            <th className="py-1.5">P</th>
            <th className="py-1.5 pr-2">L</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {datos.lecturas.map((lectura) => (
            <tr key={`${lectura.fecha}-${lectura.tipo_toma}-${lectura.valor}`}>
              <td className="py-2 pl-2">{formatFecha(lectura.fecha)}</td>
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
              <td className="py-2 pr-2">
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
    </div>
  );
}

function Fila({ label, valor, destacado }: { label: string; valor: React.ReactNode; destacado?: boolean }) {
  return (
    <>
      <dt className="text-muted-foreground">{label}</dt>
      <dd
        className={cn(
          "text-right tabular-nums",
          destacado && "font-heading text-base font-extrabold text-brand-orange",
        )}
      >
        {valor}
      </dd>
    </>
  );
}

/** Detalle completo de la pareja P/L (paridad con `PanelCandidatos.razor`):
 * Δ días y "Días L → fecha obj." son ACTIVOS (ya descuentan recesos, salen
 * del motor); Δ contador es la resta cruda de las dos lecturas elegidas. */
function DetalleParL({
  seleccion,
  calculo,
  ultimoFacturado,
}: {
  seleccion: Seleccion;
  calculo: Calculo;
  ultimoFacturado: number;
}) {
  const deltaContador =
    seleccion.partida && seleccion.llegada ? seleccion.llegada.valor - seleccion.partida.valor : null;
  const imp30d = calculo.tasaDiaria !== null ? Math.round(calculo.tasaDiaria * 30) : null;
  const esPosterior = calculo.diasProyectados !== null && calculo.diasProyectados < 0;

  return (
    <>
      <Fila label="Δ días (P → L)" valor={calculo.diasParPl ?? "—"} />
      <Fila label="Δ contador" valor={deltaContador !== null ? numberFormat.format(deltaContador) : "—"} />
      <Fila
        label="Promedio diario"
        valor={`${calculo.tasaDiaria !== null ? decimalFormat.format(calculo.tasaDiaria) : "—"} /día`}
      />
      <Fila label="Imp. 30d" valor={imp30d !== null ? numberFormat.format(imp30d) : "—"} />
      <Fila label="Días L → fecha obj." valor={calculo.diasProyectados ?? "—"} />
      <Fila label="Estim. propuesto" valor={calculo.estim !== null ? numberFormat.format(calculo.estim) : "—"} destacado />
      <Fila label="Últ. facturado" valor={numberFormat.format(ultimoFacturado)} />
      <Fila
        label="Impresiones"
        valor={calculo.impresiones !== null ? numberFormat.format(calculo.impresiones) : "—"}
        destacado
      />
      {esPosterior && (
        <p className="col-span-2 rounded-[6px] bg-warning/10 px-2 py-1.5 text-[11px] text-warning">
          ⚠ La Llegada es posterior a la fecha objetivo — el estimado se interpola hacia atrás.
        </p>
      )}
    </>
  );
}

interface ProyeccionCalculoPanelProps {
  seleccion: Seleccion;
  calculoVisible: Calculo | null;
  forzado: Calculo | null;
  puedeGestionar: boolean;
  forzando: MetodoForzado | null;
  onForzar: (metodo: MetodoForzado) => void;
  ultimoFacturado: number;
}

export function ProyeccionCalculoPanel({
  seleccion,
  calculoVisible,
  forzado,
  puedeGestionar,
  forzando,
  onForzar,
  ultimoFacturado,
}: ProyeccionCalculoPanelProps) {
  return (
    <>
      <p className="mb-2 mt-6 text-[10.5px] font-bold uppercase tracking-wide text-muted-foreground">
        Cálculo
      </p>
      <dl className="grid grid-cols-2 gap-y-2 text-[12.5px]">
        <Fila
          label="P → L"
          valor={`${seleccion.partida ? formatFecha(seleccion.partida.fecha) : "—"} → ${
            seleccion.llegada ? formatFecha(seleccion.llegada.fecha) : "—"
          }`}
        />
        {calculoVisible ? (
          <DetalleParL seleccion={seleccion} calculo={calculoVisible} ultimoFacturado={ultimoFacturado} />
        ) : forzado ? (
          <>
            <Fila
              label="Estim. propuesto"
              valor={forzado.estim !== null ? numberFormat.format(forzado.estim) : "—"}
              destacado
            />
            <Fila
              label="Impresiones del período"
              valor={forzado.impresiones !== null ? numberFormat.format(forzado.impresiones) : "—"}
              destacado
            />
            <Fila label="Método forzado" valor={<span className="text-xs">{forzado.metodoDetalle}</span>} />
          </>
        ) : (
          <>
            <Fila label="Estim. propuesto" valor="—" destacado />
            <Fila label="Impresiones del período" valor="—" destacado />
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
