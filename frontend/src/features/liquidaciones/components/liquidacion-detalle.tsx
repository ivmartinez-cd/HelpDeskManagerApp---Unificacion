"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AlertTriangle, Calendar, DollarSign, ExternalLink } from "lucide-react";
import { Spinner } from "@/shared/components/ui/spinner";
import { ApiError } from "@/services/http-client";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  Alerta,
  EstadoLiquidacion,
  LiquidacionDetalle,
  PrestadorLiquidacion,
} from "../types/liquidaciones";
import { formatARS } from "../lib/format";
import { AlertasSeccion } from "./alertas-seccion";
import { AyCAccionesBar } from "./ayc-acciones-bar";
import { EstadoBadge } from "./estado-badge";
import { EstadoSelector } from "./estado-selector";
import { ExtraItemSeccion } from "./extra-item-seccion";
import { IncidentesSeccion } from "./incidentes-seccion";
import { KpiTile } from "./kpi-tile";
import { ModeloFacturacionSeccion } from "./modelo-facturacion-seccion";
import { ObservacionesSeccion } from "./observaciones-seccion";

export function LiquidacionDetalleView({ id }: { id: string }) {
  const router = useRouter();
  const [detalle, setDetalle] = useState<LiquidacionDetalle | null>(null);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [reanalizing, setReanalizing] = useState(false);
  const [updatingEstado, setUpdatingEstado] = useState(false);
  const [soloConAlertas, setSoloConAlertas] = useState(false);

  const load = useCallback(
    () =>
      Promise.all([liquidacionesApi.get(id), liquidacionesApi.listPrestadores(false)])
        .then(([det, prest]) => {
          setDetalle(det);
          setPrestadores(prest);
        })
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 404) setNotFound(true);
          else throw err;
        })
        .finally(() => setLoading(false)),
    [id],
  );

  useEffect(() => { void load(); }, [load]);

  // Refresh silencioso al abrir el detalle: reconcilia esta liquidación contra
  // AyC (estado, costos/km de incidentes) una sola vez por visita a la página.
  // Best-effort — un fallo acá nunca debe impedir ver el detalle ya cargado.
  const reconciliadoRef = useRef(false);
  useEffect(() => {
    if (!detalle || reconciliadoRef.current) return;
    reconciliadoRef.current = true;
    const { numeroLiquidacion, estado } = detalle.liquidacion;
    if (!numeroLiquidacion || estado === "aprobada" || estado === "cerrada") return;
    void liquidacionesApi
      .reconciliar(id)
      .catch(() => {})
      .then(() => load());
  }, [detalle, id, load]);

  const handleReanalizar = async () => {
    setReanalizing(true);
    try {
      await liquidacionesApi.reanalyze(id);
      await load();
    } finally {
      setReanalizing(false);
    }
  };

  const handleUpdateEstado = async (nuevoEstado: EstadoLiquidacion) => {
    if (!detalle) return;
    setUpdatingEstado(true);
    try {
      const updated = await liquidacionesApi.updateEstado(id, nuevoEstado);
      setDetalle({ ...detalle, liquidacion: updated });
    } finally {
      setUpdatingEstado(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (notFound || !detalle) {
    return (
      <div className="flex flex-col items-center gap-4 p-16">
        <p className="font-heading text-xl font-extrabold text-foreground">
          Liquidación no encontrada
        </p>
        <p className="font-body text-sm text-muted-foreground">
          Puede que se haya eliminado o que el enlace sea viejo.
        </p>
        <Link
          href="/liquidaciones/lista"
          className="font-body text-sm font-semibold text-brand-orange hover:underline"
        >
          ← Volver a la lista de liquidaciones
        </Link>
      </div>
    );
  }

  const { liquidacion, incidentes, alertas, observaciones } = detalle;
  const pstMap = Object.fromEntries(prestadores.map((p) => [p.id, p]));
  const pst = pstMap[liquidacion.prestadorId];
  const alertasByInc = alertas.reduce<Record<string, Alerta[]>>((acc, a) => {
    (acc[a.incidenteId] ??= []).push(a);
    return acc;
  }, {});
  const incConAlertas = Object.keys(alertasByInc).length;
  const correctivos = incidentes.filter((i) => i.tipo.toLowerCase() !== "preventivo");
  const preventivos = incidentes.filter((i) => i.tipo.toLowerCase() === "preventivo");

  return (
    <div className="flex flex-col gap-5 p-6">
      <Link
        href="/liquidaciones/lista"
        className="flex w-fit items-center gap-1.5 font-body text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        ← Lista de liquidaciones
      </Link>

      {/* Header */}
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
            onClick={() => void handleReanalizar()}
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
              value={liquidacion.totalAlertas.toLocaleString("es-AR")}
              warn={liquidacion.totalAlertas > 0}
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
                <span className="font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground">
                  Cambiar estado
                </span>
                <EstadoSelector
                  estado={liquidacion.estado}
                  disabled={updatingEstado}
                  onCambiar={(nuevo) => void handleUpdateEstado(nuevo)}
                />
              </div>
            )}
            <AyCAccionesBar
              liquidacion={liquidacion}
              onActualizado={(updated) => setDetalle({ ...detalle, liquidacion: updated })}
              onAnulado={() => router.push("/liquidaciones/lista")}
            />
          </div>
        </div>
      </div>

      {/* Banner de alertas */}
      {incConAlertas > 0 && (
        <div className="flex items-center justify-between gap-4 rounded-[12px] border border-brand-orange/30 bg-brand-orange/10 px-5 py-4">
          <div className="flex items-start gap-3">
            <AlertTriangle size={16} className="mt-0.5 flex-shrink-0 text-brand-orange" />
            <p className="font-body text-sm text-foreground">
              <span className="font-semibold">
                Los {incConAlertas} incidentes tienen alertas de validación.
              </span>{" "}
              Revisá los importes cobrados contra los esperados antes de aprobar.
            </p>
          </div>
          {soloConAlertas ? (
            <button
              onClick={() => setSoloConAlertas(false)}
              className="flex-shrink-0 font-body text-sm text-brand-orange hover:underline"
            >
              Mostrar todos
            </button>
          ) : (
            <button
              onClick={() => setSoloConAlertas(true)}
              className="flex-shrink-0 font-body text-sm text-brand-orange hover:underline"
            >
              Ver sólo con alertas →
            </button>
          )}
        </div>
      )}

      <ExtraItemSeccion
        liquidacion={liquidacion}
        onUpdated={(updated) => setDetalle({ ...detalle, liquidacion: updated })}
      />

      <IncidentesSeccion
        titulo="Correctivos"
        accentClass="text-brand-orange"
        incidentes={correctivos}
        alertasByInc={alertasByInc}
        soloConAlertas={soloConAlertas}
      />
      {preventivos.length > 0 && (
        <IncidentesSeccion
          titulo="Preventivos"
          accentClass="text-emerald-500"
          incidentes={preventivos}
          alertasByInc={alertasByInc}
          soloConAlertas={soloConAlertas}
        />
      )}

      <ModeloFacturacionSeccion incidentes={incidentes} totalImporte={liquidacion.totalImporte} />

      <AlertasSeccion
        liquidacionId={id}
        alertas={alertas}
        incidentes={incidentes}
        onChanged={() => void load()}
      />

      <ObservacionesSeccion
        liquidacionId={id}
        observaciones={observaciones}
        onChanged={() => void load()}
      />
    </div>
  );
}
