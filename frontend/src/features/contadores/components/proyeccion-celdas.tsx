"use client";

import { cn } from "@/shared/utils/cn";
import type { FilaProyeccion, Semaforo } from "../types/proyeccion";
import { DetalleEstimacionTooltip, tieneDetalleEstimacion } from "./detalle-estimacion-tooltip";
import { fechaCorta, fechaLarga, n0, TEC_LABEL, tipoEstim, tipoToma } from "./proyeccion-formato";

/** Celdas de la grilla con los datos y tooltips de `GrillaEstimacion.razor`
 * (v1.7), en el estilo visual de HDM. */

const SEMAFORO_DOT: Record<Semaforo, string> = {
  VERDE: "bg-success",
  AMARILLO: "bg-warning",
  NARANJA: "bg-brand-orange",
  ROJO: "bg-destructive",
};

const SEMAFORO_TOOLTIP: Record<Semaforo, string> = {
  VERDE: "Verde · Estimación entre dos reales recientes (regla 15d ok)",
  AMARILLO:
    "Amarillo · T4 (ST) en el cálculo o confirmación requerida (receso, backup/tránsito, parque cliente-tec)",
  NARANJA: "Naranja · Estimado fuera de rango del propio equipo (< 0.6× o > 1.4× Prom6FC)",
  ROJO: "Rojo · Sin historia propia (cascada T19 por modelo) o salto imposible detectado",
};

export function SemaforoCell({ fila }: { fila: FilaProyeccion }) {
  const titulo = SEMAFORO_TOOLTIP[fila.semaforo];
  return (
    <span
      aria-label={titulo}
      title={titulo}
      className={cn("inline-block h-2.5 w-2.5 rounded-full", SEMAFORO_DOT[fila.semaforo])}
    />
  );
}

/** `MesesTooltip` del legacy (umbral 6 meses Color, 12 Mono). */
function mesesTooltip(fila: FilaProyeccion): string {
  if (fila.meses_sin_real === null) return "Sin lecturas reales registradas para este equipo";
  const umbral = fila.tecnologia === "COLOR" ? 6 : 12;
  if (fila.meses_sin_real_en_alerta) {
    return `⚠ Supera ${umbral} meses sin lectura real (${TEC_LABEL[fila.tecnologia]})`;
  }
  const m = fila.meses_sin_real;
  return `Última lectura real hace ${m} mes${m === 1 ? "" : "es"}`;
}

export function MesesCell({ fila }: { fila: FilaProyeccion }) {
  return (
    <span title={mesesTooltip(fila)} className={fila.meses_sin_real_en_alerta ? "font-bold text-destructive" : ""}>
      {fila.meses_sin_real ?? "—"}
    </span>
  );
}

function CeldaContador({ valor, fecha, tipo }: { valor: string; fecha: string; tipo: string }) {
  return (
    <>
      <p className="font-semibold tabular-nums">{valor}</p>
      <p className="flex justify-end gap-1.5 text-xs text-muted-foreground">
        <span>{fecha}</span>
        <span className="font-bold">{tipo}</span>
      </p>
    </>
  );
}

export function UltimoFacturadoCell({ fila }: { fila: FilaProyeccion }) {
  return (
    <CeldaContador
      valor={n0(fila.ultimo_facturado_valor)}
      fecha={fechaCorta(fila.ultimo_facturado_fecha)}
      tipo={tipoToma(fila.ultimo_facturado_tipo)}
    />
  );
}

/** `TooltipEstim`: detalle del cálculo + guía para el operador (no va al CSV). */
function tooltipEstim(fila: FilaProyeccion): string {
  return fila.guia_operador === null ? fila.detalle_calculo : `${fila.detalle_calculo}\n${fila.guia_operador}`;
}

/** Fila real: el contador actual ya cargado (verde). A estimar: el estimado
 * a la fecha objetivo, con el borde amarillo de un T4 sin revisar. */
export function AFacturarCell({ fila, fechaObjetivo }: { fila: FilaProyeccion; fechaObjetivo: string | null }) {
  if (fila.es_real) {
    return (
      <div
        title="Contador real registrado para el período."
        className="rounded-[6px] border border-success/60 bg-success/10 px-1.5 py-0.5 text-success"
      >
        <CeldaContador
          valor={n0(fila.estim_propuesto)}
          fecha={fechaCorta(fila.fecha_toma_actual)}
          tipo={tipoToma(fila.tipo_toma)}
        />
      </div>
    );
  }
  return (
    <div
      title={tooltipEstim(fila)}
      className={cn(
        "px-1.5 py-0.5 text-info",
        fila.t4_sin_revisar && "rounded-[6px] border border-warning bg-warning/10 [&_span.font-bold]:text-warning",
      )}
    >
      <CeldaContador
        valor={n0(fila.estim_propuesto)}
        fecha={fechaObjetivo ? fechaLarga(fechaObjetivo) : ""}
        tipo={tipoEstim(fila.tipo_toma)}
      />
    </div>
  );
}

export function ImpresionesCell({ fila }: { fila: FilaProyeccion }) {
  const tono =
    fila.coloreo === "AZUL" ? "text-info" : fila.coloreo === "NARANJA" ? "text-brand-orange" : "text-foreground";
  const numero = (
    <span
      className={cn(
        "font-bold tabular-nums",
        tono,
        fila.borde_salto_imposible && "rounded-[8px] border-2 border-dashed border-destructive px-2 py-0.5",
      )}
    >
      {n0(fila.impresiones)}
      {tieneDetalleEstimacion(fila) && <sup className="ml-0.5 cursor-help text-[9px] text-muted-foreground">i</sup>}
    </span>
  );
  if (!tieneDetalleEstimacion(fila)) return numero;
  return (
    <DetalleEstimacionTooltip fila={fila} className="inline-block">
      {numero}
    </DetalleEstimacionTooltip>
  );
}

/** Columna "Ubicación" (rowspan del equipo). */
export function UbicacionCell({ fila }: { fila: FilaProyeccion }) {
  return (
    <>
      <p className="font-semibold text-foreground">{fila.empresa}</p>
      <p className="text-xs text-muted-foreground">{fila.sucursal}</p>
      {fila.sector && <p className="text-xs text-info">Sector: {fila.sector}</p>}
    </>
  );
}

const ESTADO_LABEL = { NORMAL: null, BACKUP: "Backup", EN_TRANSITO: "En tránsito" } as const;

/** Columna "Modelo": modelo, estado de la máquina y, si se movió de empresa
 * desde el cierre del proceso, "Ubic Actual". */
export function ModeloCell({ fila }: { fila: FilaProyeccion }) {
  // Sin descripción de Siges (modo ejemplo) se rotula por el estado.
  const estado = fila.estado_maquina_desc || ESTADO_LABEL[fila.estado_maquina];
  return (
    <>
      <p className="truncate font-semibold" title={fila.modelo}>
        {fila.modelo}
      </p>
      {estado && (
        <p className={cn("text-xs", fila.estado_maquina === "NORMAL" ? "text-muted-foreground" : "font-bold text-warning")}>
          {estado}
        </p>
      )}
      {fila.empresa_actual_desc && (
        <p
          className="text-xs font-semibold text-brand-orange"
          title="La máquina se movió a otra empresa desde el cierre del proceso. Lo que se factura es la ubicación del snapshot."
        >
          Ubic Actual: {fila.empresa_actual_desc}
        </p>
      )}
    </>
  );
}
