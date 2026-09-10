"use client";

import { useCallback, useEffect, useState } from "react";
import { Spinner } from "@/shared/components/ui/spinner";
import { KpiGrid, KpiTile } from "@/shared/components/ui/kpi-tile";
import { toast } from "sonner";
import { useSession } from "@/services/session-provider";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  FacturadoPorPeriodoItem,
  Liquidacion,
  PrestadorLiquidacion,
  RankingPrestador,
} from "../types/liquidaciones";
import { formatARS } from "../lib/format";
import { FacturadoEvolucionChart } from "./facturado-evolucion-chart";
import { LiquidacionesImportModal } from "./liquidaciones-import-modal";
import { RankingPrestadoresTabla } from "./ranking-prestadores-tabla";

export function LiquidacionesDashboard() {
  const { can } = useSession();
  const puedeCrear = can("liquidaciones", "create");
  const [liquidaciones, setLiquidaciones] = useState<Liquidacion[]>([]);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [facturadoPorPeriodo, setFacturadoPorPeriodo] = useState<FacturadoPorPeriodoItem[]>([]);
  const [ranking, setRanking] = useState<RankingPrestador[]>([]);
  const [loading, setLoading] = useState(true);
  const [importOpen, setImportOpen] = useState(false);
  const [syncing, setSyncing] = useState(false);

  // Sin setLoading(true) sincrónico — ver nota en liquidaciones-lista.tsx.
  // listAll() usa fetchCatalogoCompleto para evitar el truncamiento silencioso.
  // `prestadores` solo alimenta el select del modal de importación — el
  // ranking/gráfico ya vienen agregados por nombre desde el backend.
  const load = useCallback(async () => {
    try {
      const [liqs, prest, facturado, top] = await Promise.all([
        liquidacionesApi.listAll(),
        liquidacionesApi.listPrestadores(),
        liquidacionesApi.getFacturadoPorPeriodo(),
        liquidacionesApi.getRankingPrestadores(),
      ]);
      setLiquidaciones(liqs);
      setPrestadores(prest);
      setFacturadoPorPeriodo(facturado);
      setRanking(top);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const pendientes = liquidaciones.filter(
    (l) =>
      l.estado === "abierta" ||
      l.estado === "preliquidada" ||
      l.estado === "recibida" ||
      l.estado === "observada",
  ).length;
  const totalIncidentes = liquidaciones.reduce((s, l) => s + l.totalIncidentes, 0);
  const totalImporte = liquidaciones.reduce((s, l) => s + l.totalImporte, 0);

  const handleSincronizar = async () => {
    setSyncing(true);
    try {
      const res = await liquidacionesApi.sincronizar();
      const revisadas = res.reconciliadas > 0
        ? ` (${res.reconciliadas} revisada${res.reconciliadas !== 1 ? "s" : ""} contra AyC${res.estadosActualizados > 0 ? `, ${res.estadosActualizados} con estado actualizado` : ""}${res.periodosActualizados > 0 ? `, ${res.periodosActualizados} con período actualizado` : ""}${res.extrasActualizados > 0 ? `, ${res.extrasActualizados} con ítem extra actualizado` : ""}${res.facturasActualizadas > 0 ? `, ${res.facturasActualizadas} con nº de factura actualizado` : ""})`
        : "";
      const detalle = `${res.creadas} nueva${res.creadas !== 1 ? "s" : ""}, ${res.yaExistentes} ya existentes${revisadas}${res.sinPrestador > 0 ? `, ${res.sinPrestador} sin prestador vinculado` : ""}${res.anuladas > 0 ? `, ${res.anuladas} anulada${res.anuladas !== 1 ? "s" : ""} en AyC eliminada${res.anuladas !== 1 ? "s" : ""}` : ""}`;
      if (res.fallidas > 0) {
        toast.warning(
          `Sync con fallas — ${detalle}, ${res.fallidas} con detalle SOAP fallido (se reintentan en el próximo sync)`,
        );
      } else {
        toast.success(`Sync OK — ${detalle}`);
      }
      if (res.creadas > 0 || res.reconciliadas > 0 || res.anuladas > 0) await load();
    } catch {
      toast.error("Error al sincronizar con Canal Directo");
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-xl font-extrabold text-foreground">Liquidaciones PST</h1>
        <div className="flex items-center gap-2">
          {/* Sincronizar e importar crean liquidaciones: liquidaciones.create
              (liquidaciones_ayc_router.py / liquidaciones_router.py). */}
          {puedeCrear && (
            <>
              <button
                onClick={() => void handleSincronizar()}
                disabled={syncing}
                className="rounded-[8px] border border-border bg-card px-4 py-2.5 font-body text-sm font-semibold text-foreground transition-opacity hover:opacity-70 disabled:opacity-50"
              >
                {syncing ? "Sincronizando..." : "↻ Sincronizar CD"}
              </button>
              <button
                onClick={() => setImportOpen(true)}
                className="rounded-[8px] bg-brand-orange px-4 py-2.5 font-body text-sm font-semibold text-white transition-opacity hover:opacity-90"
              >
                + Importar liquidación
              </button>
            </>
          )}
        </div>
      </div>

      <KpiGrid className="lg:grid-cols-4">
        <KpiTile
          label="Liquidaciones pendientes"
          value={String(pendientes)}
          hint={`de ${liquidaciones.length} en total`}
          tone="orange"
        />
        <KpiTile label="Total importadas" value={String(liquidaciones.length)} tone="neutral" />
        <KpiTile
          label="Total incidentes"
          value={totalIncidentes.toLocaleString("es-AR")}
          tone="neutral"
        />
        <KpiTile label="Total facturado" value={formatARS(totalImporte)} tone="neutral" />
      </KpiGrid>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="flex flex-col gap-2 rounded-[12px] border border-border bg-card p-4">
          <span className="font-heading text-[13px] font-bold text-foreground">
            Evolución de facturado — {new Date().getFullYear()}
          </span>
          <FacturadoEvolucionChart items={facturadoPorPeriodo} />
        </div>

        <div className="rounded-[12px] border border-border bg-card p-4">
          <span className="font-heading text-[13px] font-bold text-foreground">
            Ranking de prestadores por facturado
          </span>
          <div className="mt-3">
            <RankingPrestadoresTabla items={ranking} />
          </div>
        </div>
      </div>

      <LiquidacionesImportModal
        isOpen={importOpen}
        onClose={() => setImportOpen(false)}
        prestadores={prestadores}
        onSuccess={load}
      />
    </div>
  );
}
