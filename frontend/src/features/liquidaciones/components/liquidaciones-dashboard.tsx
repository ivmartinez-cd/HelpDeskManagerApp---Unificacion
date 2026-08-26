"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Spinner } from "@/shared/components/ui/spinner";
import { KpiGrid, KpiTile } from "@/shared/components/ui/kpi-tile";
import { toast } from "sonner";
import { useSession } from "@/services/session-provider";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { Liquidacion, PrestadorLiquidacion } from "../types/liquidaciones";
import { formatARS } from "../lib/format";
import { LiquidacionesDashboardTabla } from "./liquidaciones-dashboard-tabla";
import { LiquidacionesImportModal } from "./liquidaciones-import-modal";

function formatPeriodo(periodo: string): string {
  const [year, month] = periodo.split("-");
  if (!year || !month) return periodo;
  const date = new Date(Number(year), Number(month) - 1);
  return date.toLocaleDateString("es-AR", { month: "short", year: "numeric" });
}

export function LiquidacionesDashboard() {
  const { can } = useSession();
  const puedeCrear = can("liquidaciones", "create");
  const [liquidaciones, setLiquidaciones] = useState<Liquidacion[]>([]);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [importOpen, setImportOpen] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [filtroPrestador, setFiltroPrestador] = useState("");
  const [filtroPeriodo, setFiltroPeriodo] = useState("");
  const [filtroAnio, setFiltroAnio] = useState("");
  const hasAutoSelected = useRef(false);

  // Sin setLoading(true) sincrónico — ver nota en liquidaciones-lista.tsx.
  // listAll() usa fetchCatalogoCompleto para evitar el truncamiento silencioso.
  const load = useCallback(async () => {
    try {
      const [liqs, prest] = await Promise.all([
        liquidacionesApi.listAll(),
        liquidacionesApi.listPrestadores(),
      ]);
      setLiquidaciones(liqs);
      setPrestadores(prest);
      if (!hasAutoSelected.current && liqs.length > 0) {
        const periodos = [...new Set(liqs.map((l) => l.periodo))].sort().reverse();
        if (periodos[0]) {
          setFiltroPeriodo(periodos[0]);
          hasAutoSelected.current = true;
        }
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const periodosDisponibles = useMemo(
    () => [...new Set(liquidaciones.map((l) => l.periodo))].sort().reverse(),
    [liquidaciones],
  );

  const aniosDisponibles = useMemo(
    () => [...new Set(liquidaciones.map((l) => l.periodo.slice(0, 4)))].sort().reverse(),
    [liquidaciones],
  );

  const filtradas = useMemo(
    () =>
      liquidaciones.filter(
        (l) =>
          (!filtroPrestador || l.prestadorId === filtroPrestador) &&
          (!filtroPeriodo || l.periodo === filtroPeriodo) &&
          (!filtroAnio || l.periodo.startsWith(filtroAnio)),
      ),
    [liquidaciones, filtroPrestador, filtroPeriodo, filtroAnio],
  );

  const prestadorMap = Object.fromEntries(prestadores.map((p) => [p.id, p]));
  const pendientes = filtradas.filter(
    (l) =>
      l.estado === "abierta" ||
      l.estado === "preliquidada" ||
      l.estado === "recibida" ||
      l.estado === "observada",
  ).length;
  const totalIncidentes = filtradas.reduce((s, l) => s + l.totalIncidentes, 0);
  const totalImporte = filtradas.reduce((s, l) => s + l.totalImporte, 0);
  const ultimas = filtradas.slice(0, 10);

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

  const selectCls =
    "rounded-[8px] border border-border bg-card px-3 py-2 font-body text-sm text-foreground outline-none focus:border-brand-orange/70";

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

      <div className="flex flex-wrap items-center gap-3">
        <select
          value={filtroPrestador}
          onChange={(e) => setFiltroPrestador(e.target.value)}
          className={selectCls}
          aria-label="Filtrar por prestador"
        >
          <option value="">Todos los prestadores</option>
          {prestadores.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nombreCorto}
            </option>
          ))}
        </select>

        <select
          value={filtroPeriodo}
          onChange={(e) => setFiltroPeriodo(e.target.value)}
          className={selectCls}
          aria-label="Filtrar por período"
        >
          <option value="">Todos los períodos</option>
          {periodosDisponibles.map((p) => (
            <option key={p} value={p}>
              {formatPeriodo(p)}
            </option>
          ))}
        </select>

        <select
          value={filtroAnio}
          onChange={(e) => setFiltroAnio(e.target.value)}
          className={selectCls}
          aria-label="Filtrar por año"
        >
          <option value="">Todos los años</option>
          {aniosDisponibles.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>

        <span className="font-body text-sm text-muted-foreground">
          {filtradas.length} liquidaci{filtradas.length === 1 ? "ón" : "ones"}
        </span>
      </div>

      <KpiGrid className="lg:grid-cols-4">
        <KpiTile
          label="Liquidaciones pendientes"
          value={String(pendientes)}
          hint={`de ${filtradas.length} en total`}
          tone="orange"
        />
        <KpiTile label="Total importadas" value={String(filtradas.length)} tone="neutral" />
        <KpiTile
          label="Total incidentes"
          value={totalIncidentes.toLocaleString("es-AR")}
          tone="neutral"
        />
        <KpiTile label="Total facturado" value={formatARS(totalImporte)} tone="neutral" />
      </KpiGrid>

      <LiquidacionesDashboardTabla ultimas={ultimas} prestadorMap={prestadorMap} />

      <LiquidacionesImportModal
        isOpen={importOpen}
        onClose={() => setImportOpen(false)}
        prestadores={prestadores}
        onSuccess={load}
      />
    </div>
  );
}
