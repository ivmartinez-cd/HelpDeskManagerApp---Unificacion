"use client";

import { AlertTriangle, Calendar, DollarSign, ExternalLink, Receipt } from "lucide-react";
import type {
  EstadoLiquidacion,
  Liquidacion,
  PrestadorLiquidacion,
} from "../types/liquidaciones";
import { formatARS } from "../lib/format";
import { AyCAccionesBar } from "./ayc-acciones-bar";
import { EstadoBadge } from "./estado-badge";
import { EstadoSelector } from "./estado-selector";
import { KpiTile } from "./kpi-tile";

export function LiquidacionDetalleHeader({
  liquidacion,
  alertasPendientes,
  pst,
  reanalizing,
  onReanalizar,
  updatingEstado,
  onUpdateEstado,
  onActualizado,
  onAnulado,
}: {
  liquidacion: Liquidacion;
  /** Alertas en estado pendiente/en_revision — a diferencia de
   * `liquidacion.totalAlertas` (fijo por el motor de reglas al importar/reanalizar),
   * baja en vivo cuando la TL resuelve o descarta una alerta. */
  alertasPendientes: number;
  pst: PrestadorLiquidacion | undefined;
  reanalizing: boolean;
  onReanalizar: () => void;
  updatingEstado: boolean;
  onUpdateEstado: (nuevo: EstadoLiquidacion) => void;
  onActualizado: (updated: Liquidacion) => void;
  onAnulado: () => void;
}) {
  return (
    <div className="rounded-[12px] border border-border bg-card p-5">
      {/* Row 1: título + estado badge | reanalizar */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="font-heading text-2xl font-extrabold text-foreground">
            {liquidacion.nombreArchivo ?? `Liquidación ${liquidacion.periodo}`}
          </h1>
          <EstadoBadge estado={liquidacion.estado} />
        </div>
        <button
          onClick={onReanalizar}
          disabled={reanalizing}
          className="flex-shrink-0 rounded-[8px] bg-brand-orange px-4 py-2.5 font-body text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {reanalizing ? "Reanalizando..." : "↻ Reanalizar"}
        </button>
      </div>

      {/* Row 2: breadcrumbs */}
      <div className="mt-2 flex flex-wrap items-center gap-1.5 font-body text-sm text-muted-foreground">
        {pst && (
          <>
            <span>{pst.region ?? pst.nombreCorto} — {pst.nombre}</span>
            <span>·</span>
          </>
        )}
        <span>Período {liquidacion.periodo}</span>
        <span>·</span>
        <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs">
          {liquidacion.tipoLiquidacion}
        </span>
        {liquidacion.numeroLiquidacion && (
          <>
            <span>·</span>
            <a
              href={`https://webagentes.canaldirecto.com.ar/liquidations/view/${liquidacion.numeroLiquidacion}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-brand-orange hover:underline"
            >
              Remito {liquidacion.numeroLiquidacion}
              <ExternalLink size={12} />
            </a>
          </>
        )}
        {liquidacion.numeroFactura && (
          <>
            <span>·</span>
            {liquidacion.facturaPdfUrl ? (
              <a
                href={liquidacion.facturaPdfUrl}
                target="_blank"
                rel="noopener noreferrer"
                title={`Factura ${liquidacion.numeroFactura}`}
                aria-label={`Ver factura ${liquidacion.numeroFactura}`}
                className="inline-flex items-center text-brand-orange hover:underline"
              >
                <Receipt size={14} />
              </a>
            ) : (
              <span>Factura {liquidacion.numeroFactura}</span>
            )}
          </>
        )}
      </div>

      {/* Row 3: KPIs | cambiar estado + acciones */}
      <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-wrap items-stretch gap-3">
          <KpiTile
            icon={<Calendar size={16} />}
            label="Incidentes"
            value={liquidacion.totalIncidentes.toLocaleString("es-AR")}
          />
          <KpiTile
            icon={<AlertTriangle size={16} />}
            label="Alertas"
            value={alertasPendientes.toLocaleString("es-AR")}
            warn={alertasPendientes > 0}
          />
          <KpiTile
            icon={<DollarSign size={16} />}
            label="Total facturado"
            value={formatARS(liquidacion.totalImporte)}
          />
        </div>
        <div className="flex flex-col items-end gap-2">
          {!liquidacion.numeroLiquidacion && (
            <div className="flex items-center gap-2">
              <span
                className="font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground"
                title="Liquidación manual, sin remito de Canal Directo — el estado se cambia acá a mano en vez de sincronizarse con AyC"
              >
                Cambiar estado
              </span>
              <EstadoSelector
                estado={liquidacion.estado}
                disabled={updatingEstado}
                onCambiar={onUpdateEstado}
              />
            </div>
          )}
          <AyCAccionesBar
            liquidacion={liquidacion}
            onActualizado={onActualizado}
            onAnulado={onAnulado}
          />
        </div>
      </div>
    </div>
  );
}
