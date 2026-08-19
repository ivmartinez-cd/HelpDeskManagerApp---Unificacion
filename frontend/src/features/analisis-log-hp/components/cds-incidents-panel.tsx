"use client";

import { useEffect, useState } from "react";
import { analisisLogHpApi } from "../api/analisis-log-hp-api";
import type { CdsIncident } from "../types/analisis-log-hp";
import { formatIncidentNumber } from "../utils/check-digit";

function CounterCell({ contador }: { contador: string | null }) {
  if (!contador) return <span className="text-muted-foreground">—</span>;
  const n = Number.parseInt(contador, 10);
  return <>{Number.isNaN(n) ? contador : n.toLocaleString("es-AR")}</>;
}

function ReplacementsCell({ inc }: { inc: CdsIncident }) {
  if (!inc.repuestos.length) return <span className="text-muted-foreground">—</span>;
  return (
    <div className="flex flex-wrap gap-1">
      {inc.repuestos.map((r, idx) => (
        <span
          key={idx}
          className="rounded-full border border-border bg-white/[.03] px-2 py-0.5 font-body text-[10px] text-foreground"
        >
          {r.articulo} (x{r.cantidad})
        </span>
      ))}
    </div>
  );
}

function JobsCell({ inc }: { inc: CdsIncident }) {
  if (!inc.tareas_realizadas.length) return <span className="text-muted-foreground">—</span>;
  return (
    <ul className="list-disc pl-4 font-body text-[11px] text-foreground/90">
      {inc.tareas_realizadas.map((job, idx) => (
        <li key={idx}>{job}</li>
      ))}
    </ul>
  );
}

function IncidentsTable({ incidents }: { incidents: CdsIncident[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left" style={{ minWidth: 720 }}>
        <thead>
          <tr className="border-b border-border/50">
            {["Fecha", "Incidente", "Motivo", "Repuestos", "Tareas realizadas", "Contador"].map((h) => (
              <th key={h} className="py-1.5 pr-4 font-body text-[10px] font-bold uppercase tracking-wide text-muted-foreground">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {incidents.map((inc) => (
            <tr key={inc.id || inc.numero_incidente} className="border-b border-border/30 hover:bg-white/[.02] align-top">
              <td className="py-2 pr-4 font-body text-[11px] text-muted-foreground">{inc.fecha}</td>
              <td className="py-2 pr-4 font-body text-[12px]">
                <a
                  href={`https://webagentes.canaldirecto.com.ar/incidents/view/${formatIncidentNumber(inc.numero_incidente)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand-orange hover:underline"
                >
                  {formatIncidentNumber(inc.numero_incidente)}
                </a>
              </td>
              <td className="py-2 pr-4 font-body text-[12px] text-foreground">{inc.motivo}</td>
              <td className="py-2 pr-4"><ReplacementsCell inc={inc} /></td>
              <td className="py-2 pr-4"><JobsCell inc={inc} /></td>
              <td className="py-2 pr-4 font-body text-[12px] text-foreground">
                <CounterCell contador={inc.contador} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function CdsIncidentsPanel({ serial }: { serial: string }) {
  const [incidents, setIncidents] = useState<CdsIncident[] | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!loaded) return;
    let cancelled = false;
    analisisLogHpApi.getCdsIncidents(serial)
      .then((data) => { if (!cancelled) setIncidents(data); })
      .catch(() => { if (!cancelled) setIncidents([]); });
    return () => { cancelled = true; };
  }, [serial, loaded]);

  if (!loaded) {
    return (
      <button
        type="button"
        onClick={() => setLoaded(true)}
        className="font-body text-[12px] text-brand-orange hover:underline"
      >
        Cargar incidentes de Canal Directo →
      </button>
    );
  }
  if (incidents === null) {
    return <p className="font-body text-[13px] text-muted-foreground">Consultando incidentes en Canal Directo…</p>;
  }
  if (!incidents.length) {
    return (
      <p className="font-body text-[13px] text-muted-foreground">
        Sin incidentes reportados en los últimos 12 meses.
      </p>
    );
  }
  return <IncidentsTable incidents={incidents} />;
}
