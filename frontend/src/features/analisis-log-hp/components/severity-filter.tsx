"use client";

import type { Severity } from "../types/analisis-log-hp";
import { SEV_COLOR } from "../utils/analysis-utils";

interface Props {
  active: Set<Severity>;
  onChange: (s: Set<Severity>) => void;
}

const SEVERITIES: Severity[] = ["ERROR", "WARNING", "INFO"];

export function SeverityFilter({ active, onChange }: Props) {
  function toggle(sev: Severity) {
    const next = new Set(active);
    if (next.has(sev)) next.delete(sev);
    else next.add(sev);
    onChange(next);
  }

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="font-body text-[10px] font-bold uppercase tracking-[.05em] text-muted-foreground">
        FILTRAR ANÁLISIS:
      </span>
      {SEVERITIES.map((sev) => {
        const on = active.has(sev);
        return (
          <button
            key={sev}
            type="button"
            onClick={() => toggle(sev)}
            className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 font-body text-[11px] font-black uppercase tracking-wide border transition-colors"
            style={{
              borderColor: on ? SEV_COLOR[sev] : "transparent",
              backgroundColor: on ? `${SEV_COLOR[sev]}22` : "transparent",
              color: on ? SEV_COLOR[sev] : "#6b7280",
            }}
          >
            {sev}
          </button>
        );
      })}
      {active.size > 0 && (
        <button
          type="button"
          onClick={() => onChange(new Set())}
          className="font-body text-[11px] text-muted-foreground hover:text-foreground transition-colors ml-1"
        >
          Limpiar
        </button>
      )}
    </div>
  );
}
