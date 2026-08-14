"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { Spinner } from "@/shared/components/ui/spinner";
import { KpiGrid, KpiTile } from "@/shared/components/ui/kpi-tile";
import { toast } from "sonner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { Liquidacion, PrestadorLiquidacion } from "../types/liquidaciones";
import { formatARS, formatFecha } from "../lib/format";
import { EstadoBadge } from "./estado-badge";
import { LiquidacionesImportModal } from "./liquidaciones-import-modal";

export function LiquidacionesDashboard() {
  const [liquidaciones, setLiquidaciones] = useState<Liquidacion[]>([]);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [importOpen, setImportOpen] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [filtroPrestador, setFiltroPrestador] = useState("");
  const [filtroAnio, setFiltroAnio] = useState("");

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
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const aniosDisponibles = useMemo(
    () => [...new Set(liquidaciones.map((l) => l.periodo.slice(0, 4)))].sort().reverse(),
    [liquidaciones],
  );

  const filtradas = useMemo(
    () =>
      liquidaciones.filter(
        (l) =>
          (!filtroPrestador || l.prestadorId === filtroPrestador) &&
          (!filtroAnio || l.periodo.startsWith(filtroAnio)),
      ),
    [liquidaciones, filtroPrestador, filtroAnio],
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
      const detalle = `${res.creadas} nueva${res.creadas !== 1 ? "s" : ""}, ${res.yaExistentes} ya existentes${res.sinPrestador > 0 ? `, ${res.sinPrestador} sin prestador vinculado` : ""}`;
      if (res.fallidas > 0) {
        toast.warning(
          `Sync con fallas — ${detalle}, ${res.fallidas} con detalle SOAP fallido (se reintentan en el próximo sync)`,
        );
      } else {
        toast.success(`Sync OK — ${detalle}`);
      }
      if (res.creadas > 0) await load();
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

  const thCls =
    "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
  const tdCls = "py-3 px-4 font-body text-sm text-foreground";

  const selectCls =
    "rounded-[8px] border border-border bg-card px-3 py-2 font-body text-sm text-foreground outline-none focus:border-brand-orange/70";

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-xl font-extrabold text-foreground">Liquidaciones PST</h1>
        <div className="flex items-center gap-2">
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

      <div className="overflow-hidden rounded-[12px] border border-border bg-card">
        <div className="flex items-center justify-between px-4 pt-5 pb-3">
          <h2 className="font-heading text-base font-bold text-foreground">
            Últimas liquidaciones
          </h2>
          <Link
            href="/liquidaciones/lista"
            className="font-body text-sm text-brand-orange hover:underline"
          >
            Ver todas
          </Link>
        </div>

        {ultimas.length === 0 ? (
          <p className="px-4 pb-6 font-body text-sm text-muted-foreground">
            Todavía no hay liquidaciones importadas.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-muted/40">
                  <th className={thCls}>Prestador</th>
                  <th className={thCls}>Período</th>
                  <th className={thCls}>Estado</th>
                  <th className={`${thCls} text-right`}>Incidentes</th>
                  <th className={`${thCls} text-right`}>Importe</th>
                  <th className={thCls}>Fecha de carga</th>
                  <th className={thCls}>Web Agentes</th>
                </tr>
              </thead>
              <tbody>
                {ultimas.map((liq) => {
                  const pst = prestadorMap[liq.prestadorId];
                  return (
                    <tr
                      key={liq.id}
                      className="border-t border-border transition-colors hover:bg-muted/30"
                    >
                      <td className={tdCls}>
                        {pst ? `${pst.region ?? pst.nombreCorto} — ${pst.nombre}` : liq.prestadorId.slice(0, 8)}
                      </td>
                      <td className={tdCls}>{liq.periodo || "—"}</td>
                      <td className={tdCls}>
                        <EstadoBadge estado={liq.estado} />
                      </td>
                      <td className={`${tdCls} text-right`}>
                        {liq.totalIncidentes.toLocaleString("es-AR")}
                      </td>
                      <td className={`${tdCls} text-right`}>{formatARS(liq.totalImporte)}</td>
                      <td className={`${tdCls} text-muted-foreground`}>
                        {formatFecha(liq.fechaImportacion)}
                      </td>
                      <td className={tdCls}>
                        {liq.numeroLiquidacion ? (
                          <a
                            href={`https://webagentes.canaldirecto.com.ar/liquidations/view/${liq.numeroLiquidacion}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 font-body text-sm text-brand-orange hover:underline"
                          >
                            {liq.numeroLiquidacion}
                            <ExternalLink size={12} />
                          </a>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
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
