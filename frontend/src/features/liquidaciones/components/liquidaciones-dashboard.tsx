"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { Liquidacion, PrestadorLiquidacion } from "../types/liquidaciones";
import { EstadoBadge } from "./estado-badge";
import { LiquidacionesImportModal } from "./liquidaciones-import-modal";

function formatARS(n: number) {
  return n.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 2 });
}

function formatFecha(iso: string) {
  const d = new Date(iso);
  return `${d.getDate()}/${d.getMonth() + 1}/${d.getFullYear()}`;
}

interface KpiCardProps {
  label: string;
  value: string;
  hint?: string;
  accentColor: string;
}

function KpiCard({ label, value, hint, accentColor }: KpiCardProps) {
  return (
    <div
      className="flex flex-col gap-1.5 rounded-[10px] p-5"
      style={{ background: "#1e1e1e", borderRadius: 10 }}
    >
      <span
        className="font-body text-[11px] font-bold uppercase tracking-[.08em]"
        style={{ color: "#9a9a9a" }}
      >
        {label}
      </span>
      <span className="font-heading text-2xl font-extrabold" style={{ color: accentColor }}>
        {value}
      </span>
      {hint && (
        <span className="font-body text-xs" style={{ color: "rgba(255,255,255,.35)" }}>
          {hint}
        </span>
      )}
    </div>
  );
}

export function LiquidacionesDashboard() {
  const [liquidaciones, setLiquidaciones] = useState<Liquidacion[]>([]);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [importOpen, setImportOpen] = useState(false);

  // Sin setLoading(true) sincrónico — ver nota en liquidaciones-lista.tsx.
  const load = useCallback(async () => {
    try {
      const [liqPage, prest] = await Promise.all([
        liquidacionesApi.list({ size: 200 }),
        liquidacionesApi.listPrestadores(),
      ]);
      setLiquidaciones(liqPage.items);
      setPrestadores(prest);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const prestadorMap = Object.fromEntries(prestadores.map((p) => [p.id, p]));
  const pendientes = liquidaciones.filter(
    (l) =>
      l.estado === "abierta" ||
      l.estado === "preliquidada" ||
      l.estado === "recibida" ||
      l.estado === "observada",
  ).length;
  const totalIncidentes = liquidaciones.reduce((s, l) => s + l.totalIncidentes, 0);
  const totalImporte = liquidaciones.reduce((s, l) => s + l.totalImporte, 0);
  const ultimas = liquidaciones.slice(0, 10);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner />
      </div>
    );
  }

  const thCls =
    "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
  const tdCls = "py-3 px-4 font-body text-sm";

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-xl font-extrabold text-foreground">Liquidaciones PST</h1>
        <button
          onClick={() => setImportOpen(true)}
          className="rounded-[8px] bg-brand-orange px-4 py-2.5 font-body text-sm font-semibold text-white transition-opacity hover:opacity-90"
        >
          + Importar liquidación
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard
          label="Liquidaciones pendientes"
          value={String(pendientes)}
          hint={`de ${liquidaciones.length} en total`}
          accentColor="#eab308"
        />
        <KpiCard
          label="Total importadas"
          value={String(liquidaciones.length)}
          accentColor="#e0e0e0"
        />
        <KpiCard
          label="Total incidentes"
          value={totalIncidentes.toLocaleString("es-AR")}
          accentColor="#22c55e"
        />
        <KpiCard label="Total facturado" value={formatARS(totalImporte)} accentColor="#e0e0e0" />
      </div>

      <div
        className="rounded-[12px] overflow-hidden"
        style={{ background: "#1e1e1e", border: "1px solid rgba(255,255,255,.07)" }}
      >
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
                <tr style={{ background: "rgba(0,0,0,.2)" }}>
                  <th className={thCls}>Prestador</th>
                  <th className={thCls}>Período</th>
                  <th className={thCls}>Estado</th>
                  <th className={`${thCls} text-right`}>Incidentes</th>
                  <th className={`${thCls} text-right`}>Importe</th>
                  <th className={thCls}>Fecha de carga</th>
                </tr>
              </thead>
              <tbody>
                {ultimas.map((liq) => {
                  const pst = prestadorMap[liq.prestadorId];
                  return (
                    <tr
                      key={liq.id}
                      className="border-t transition-colors hover:bg-white/[0.03]"
                      style={{ borderColor: "rgba(255,255,255,.07)" }}
                    >
                      <td className={tdCls} style={{ color: "#e0e0e0" }}>
                        {pst ? `${pst.region ?? pst.nombreCorto} — ${pst.nombre}` : liq.prestadorId.slice(0, 8)}
                      </td>
                      <td className={tdCls} style={{ color: "#e0e0e0" }}>
                        {liq.periodo || "—"}
                      </td>
                      <td className={tdCls}>
                        <EstadoBadge estado={liq.estado} />
                      </td>
                      <td className={`${tdCls} text-right`} style={{ color: "#e0e0e0" }}>
                        {liq.totalIncidentes.toLocaleString("es-AR")}
                      </td>
                      <td
                        className={`${tdCls} text-right`}
                        style={{ color: "#e0e0e0" }}
                      >
                        {formatARS(liq.totalImporte)}
                      </td>
                      <td className={tdCls} style={{ color: "rgba(255,255,255,.4)" }}>
                        {formatFecha(liq.fechaImportacion)}
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
