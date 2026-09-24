import { TriangleAlert } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import { formatArgDateTime } from "../../utils/format";
import type {
  ColorSemaforo,
  FilaDespacho,
  ResultadoAccion,
  UltimaAccionDespacho,
} from "../../types/despachados";
import {
  CLASE_RESULTADO,
  ICONO_COLOR,
  TONO,
  etiquetaChip,
  etiquetaResultado,
  etiquetaTipo,
  tieneMotivo,
  textoLimite,
} from "./semaforo";

/** Piezas chicas compartidas por la bandeja, la tabla y el panel lateral. El
 * color nunca va solo: chip = ícono + texto + color. */

const CHIP_BASE =
  "inline-flex items-center gap-[5px] whitespace-nowrap rounded-full py-[3px] pl-[7px] pr-[9px] font-body text-[10px] font-bold uppercase leading-[15px] tracking-[.03em]";

export function ChipSemaforo({
  color,
  estado,
  observacion,
}: {
  color: ColorSemaforo;
  estado: string;
  observacion: string;
}) {
  const Icono = ICONO_COLOR[color];
  return (
    <span className={cn(CHIP_BASE, TONO[color].chip)}>
      <Icono className="h-3 w-3 flex-none" aria-hidden="true" />
      {etiquetaChip(color, estado, observacion)}
    </span>
  );
}

export function ResultadoBadge({ resultado }: { resultado: ResultadoAccion }) {
  return (
    <span
      className={cn(
        "whitespace-nowrap rounded-full px-2 py-0.5 font-body text-[10px] font-bold uppercase leading-[15px] tracking-[.03em]",
        CLASE_RESULTADO[resultado],
      )}
    >
      {etiquetaResultado(resultado)}
    </span>
  );
}

/** Estado de OCA con el motivo abajo (resaltado si es un problema). */
export function EstadoOcaCelda({ fila }: { fila: FilaDespacho }) {
  if (!fila.estado) return <span className="text-muted-foreground">Sin datos en OCA</span>;
  const conMotivo = tieneMotivo(fila.motivo);
  return (
    <>
      {fila.estado}
      <span
        className={cn(
          "block text-xs",
          conMotivo ? cn("font-bold", TONO[fila.color].text) : "text-muted-foreground",
        )}
      >
        {conMotivo ? fila.motivo : "Sin Motivo"}
      </span>
    </>
  );
}

/** "Límite / aviso": plazo de retiro en rojo, observación en amarillo. */
export function LimiteCelda({ fila }: { fila: FilaDespacho }) {
  if (fila.color === "rojo" && fila.fechaLimite) {
    return (
      <span className={cn("whitespace-nowrap font-bold", TONO.rojo.text)}>
        {textoLimite(fila.fechaLimite, fila.diasHabilesParaLimite)}
      </span>
    );
  }
  if (fila.color === "amarillo" && fila.observacion) {
    return <span className={cn("font-semibold", TONO.amarillo.text)}>{fila.observacion}</span>;
  }
  if (fila.observacion) return <span className="text-muted-foreground">{fila.observacion}</span>;
  return <span className="text-muted-foreground">—</span>;
}

export function UltimaAccionCelda({ accion }: { accion: UltimaAccionDespacho | null }) {
  if (!accion) {
    return (
      <span className={cn("inline-flex items-center gap-[5px] whitespace-nowrap font-bold", TONO.naranja.text)}>
        <TriangleAlert className="h-3 w-3" aria-hidden="true" />
        Sin acción registrada
      </span>
    );
  }
  return (
    <>
      <span>
        {etiquetaTipo(accion.tipo)} · <ResultadoBadge resultado={accion.resultado} />
      </span>
      <span className="block text-xs text-muted-foreground">
        {formatArgDateTime(accion.creadaEn)} · {accion.usuarioNombre}
      </span>
    </>
  );
}

/** Número con "+N" cuando la guía agrupa más de uno (remitos, incidentes). */
export function ConExtra({ valor, cantidad }: { valor: string; cantidad: number }) {
  return (
    <>
      {valor || "—"}
      {cantidad > 1 && <span className="ml-1 text-xs text-muted-foreground">+{cantidad - 1}</span>}
    </>
  );
}

/** Clases de una fila clickeable (hover, seleccionada y foco visible). */
export function claseFila(seleccionada: boolean): string {
  return cn(
    "cursor-pointer border-b border-border outline-none transition-colors last:border-b-0 hover:bg-muted/30 focus-visible:bg-muted/40 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-brand-orange/60",
    seleccionada && "bg-brand-orange/[.08] hover:bg-brand-orange/[.08]",
  );
}

export const TH =
  "whitespace-nowrap px-3 py-2.5 text-left font-body text-[11px] font-bold uppercase tracking-[.025em] text-muted-foreground first:pl-5 last:pr-5";
export const TD = "px-3 py-[11px] align-top font-body text-[13px] leading-[18px] first:pl-5 last:pr-5";
