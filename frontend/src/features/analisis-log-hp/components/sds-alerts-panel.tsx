"use client";

import { useEffect, useState } from "react";
import { analisisLogHpApi } from "../api/analisis-log-hp-api";

type Alert = Record<string, unknown>;

const ALERT_CLASS_LABEL: Record<string, string> = {
  SYSTEM_WARNING: "Sistema",
  OTHER: "Otro",
  SUPPLY: "Consumible",
  PAPER_JAM: "Atasco de papel",
  OFFLINE: "Sin conexión",
  DOOR_OPEN: "Puerta abierta",
};

function str(a: Alert, key: string): string {
  const v = a[key];
  return typeof v === "string" ? v : "";
}

function num(a: Alert, key: string): number {
  const v = a[key];
  return typeof v === "number" ? v : 0;
}

function formatDate(iso: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("es-AR", {
    day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

function severityLabel(level: number): { label: string; color: string } {
  if (level >= 4) return { label: "Crítico", color: "#ef4444" };
  if (level >= 3) return { label: "Moderado", color: "#eab308" };
  return { label: "Bajo", color: "#3b82f6" };
}

function AlertsTable({ alerts, emptyText }: { alerts: Alert[]; emptyText: string }) {
  if (!alerts.length) return <p className="font-body text-[13px] text-muted-foreground">{emptyText}</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left" style={{ minWidth: 560 }}>
        <thead>
          <tr className="border-b border-border/50">
            {["Fecha", "Clase", "Descripción", "Severidad", "Ciclos motor", "Resuelto"].map((h) => (
              <th key={h} className="py-1.5 pr-4 font-body text-[10px] font-bold uppercase tracking-wide text-muted-foreground">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {alerts.map((a, i) => {
            const sev = severityLabel(num(a, "severityLevel"));
            const cleared = str(a, "cleared");
            const alertClass = str(a, "alertClass");
            return (
              <tr key={`${str(a, "date")}-${str(a, "mibCode")}-${i}`} className="border-b border-border/30 hover:bg-white/[.02]">
                <td className="py-2 pr-4 font-body text-[11px] text-muted-foreground">{formatDate(str(a, "date"))}</td>
                <td className="py-2 pr-4 font-body text-[12px] text-foreground">{ALERT_CLASS_LABEL[alertClass] ?? alertClass}</td>
                <td className="py-2 pr-4 font-body text-[12px] text-foreground">{str(a, "description")}</td>
                <td className="py-2 pr-4 font-body text-[11px] font-semibold" style={{ color: sev.color }}>{sev.label}</td>
                <td className="py-2 pr-4 font-body text-[12px] text-foreground">{num(a, "engineCycles").toLocaleString("es-AR")}</td>
                <td className="py-2 pr-4 font-body text-[11px]">
                  {cleared ? (
                    <span className="text-muted-foreground">{formatDate(cleared)}</span>
                  ) : (
                    <span className="text-destructive">Activa ●</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function SdsAlertsPanel({ deviceId }: { deviceId: string }) {
  const [tab, setTab] = useState<"current" | "history">("current");
  const [current, setCurrent] = useState<Alert[] | null>(null);
  const [history, setHistory] = useState<Alert[] | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!loaded) return;
    let cancelled = false;
    Promise.all([
      analisisLogHpApi.getAlerts(Number(deviceId), true),
      analisisLogHpApi.getAlerts(Number(deviceId), false),
    ])
      .then(([c, h]) => { if (!cancelled) { setCurrent(c); setHistory(h); } })
      .catch(() => { if (!cancelled) { setCurrent([]); setHistory([]); } });
    return () => { cancelled = true; };
  }, [deviceId, loaded]);

  if (!loaded) {
    return (
      <button
        type="button"
        onClick={() => setLoaded(true)}
        className="font-body text-[12px] text-brand-orange hover:underline"
      >
        Cargar alertas del portal SDS →
      </button>
    );
  }
  if (current === null || history === null) {
    return <p className="font-body text-[13px] text-muted-foreground">Consultando portal HP SDS…</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        {(["current", "history"] as const).map((t) => {
          const count = (t === "current" ? current : history).length;
          return (
            <button
              key={t}
              type="button"
              onClick={() => setTab(t)}
              className={`rounded-full px-3 py-1 font-body text-[11px] font-semibold border transition-colors ${
                tab === t
                  ? "border-brand-orange text-brand-orange bg-brand-orange/10"
                  : "border-border text-muted-foreground"
              }`}
            >
              {t === "current" ? "Activas" : "Historial"}
              {count > 0 && <span className="ml-1 opacity-70">{count}</span>}
            </button>
          );
        })}
      </div>
      {tab === "current" ? (
        <AlertsTable alerts={current} emptyText="Sin alertas activas en este momento." />
      ) : (
        <AlertsTable alerts={history} emptyText="Sin alertas en el historial." />
      )}
    </div>
  );
}
