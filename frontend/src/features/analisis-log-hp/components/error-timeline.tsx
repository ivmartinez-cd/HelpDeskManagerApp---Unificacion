"use client";

import { useState } from "react";
import type { AnalysisResult, LogEvent, Severity } from "../types/analisis-log-hp";
import {
  SEV_COLOR,
  filterEventsByDays,
  filterEventsBySeverity,
  fmtDatetime,
  normSev,
  relativeTime,
} from "../utils/analysis-utils";

interface Props {
  analysis: AnalysisResult;
  activeSeverities: Set<Severity>;
}

const TIME_RANGES = [
  { label: "1 día", days: 1 },
  { label: "3 días", days: 3 },
  { label: "7 días", days: 7 },
  { label: "14 días", days: 14 },
  { label: "Todo", days: 0 },
];

const PAGE_SIZE = 50;

export function ErrorTimeline({ analysis, activeSeverities }: Props) {
  const [days, setDays] = useState(0);
  const [page, setPage] = useState(1);

  const filtered = filterEventsBySeverity(
    filterEventsByDays(analysis.events, days),
    activeSeverities,
  ).slice().sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
  );

  const criticals = filtered.filter((e) => normSev(e.code_severity) === "ERROR").length;
  const warnings = filtered.filter((e) => normSev(e.code_severity) === "WARNING").length;
  const infos = filtered.filter((e) => normSev(e.code_severity) === "INFO").length;

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const visible = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  function handleRangeChange(d: number) {
    setDays(d);
    setPage(1);
  }

  return (
    <div className="rounded-[12px] border border-border bg-card p-4 flex flex-col gap-3">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-heading text-[13px] font-bold text-foreground">
          Timeline de errores
        </span>
        <div className="flex gap-1">
          {TIME_RANGES.map(({ label, days: d }) => (
            <button
              key={label}
              type="button"
              onClick={() => handleRangeChange(d)}
              className="rounded-full px-2.5 py-0.5 font-body text-[11px] font-semibold transition-colors"
              style={{
                background: days === d ? "#F7941D" : "transparent",
                color: days === d ? "#fff" : "#6b7280",
                border: `1px solid ${days === d ? "#F7941D" : "transparent"}`,
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Counters */}
      <div className="flex gap-3 font-body text-[12px] text-muted-foreground">
        {criticals > 0 && <span style={{ color: SEV_COLOR.ERROR }}>{criticals} críticos</span>}
        {warnings > 0 && <span style={{ color: SEV_COLOR.WARNING }}>{warnings} warnings</span>}
        {infos > 0 && <span style={{ color: SEV_COLOR.INFO }}>{infos} info</span>}
        {filtered.length === 0 && <span>Sin eventos</span>}
      </div>

      {/* List */}
      <div className="flex flex-col gap-0 divide-y divide-border/50">
        {visible.map((ev: LogEvent, i: number) => {
          const sev = normSev(ev.code_severity);
          return (
            <div key={i} className="flex items-start gap-3 py-2.5">
              <div
                className="mt-1.5 h-2 w-2 flex-none rounded-full"
                style={{ backgroundColor: SEV_COLOR[sev] }}
              />
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-baseline gap-2">
                  <span className="font-body text-[11px] text-muted-foreground">
                    {fmtDatetime(ev.timestamp)}
                  </span>
                  <span
                    className="font-mono text-[12px] font-bold"
                    style={{ color: SEV_COLOR[sev] }}
                  >
                    {ev.code}
                  </span>
                  {ev.code_description && (
                    <span className="font-body text-[12px] text-foreground/80">
                      {ev.code_description.slice(0, 64)}
                    </span>
                  )}
                </div>
              </div>
              <span className="font-body text-[11px] text-muted-foreground flex-none">
                {relativeTime(ev.timestamp)}
              </span>
            </div>
          );
        })}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-1">
          <span className="font-body text-[11px] text-muted-foreground">
            {filtered.length} eventos · pág. {page}/{totalPages}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="rounded-md px-2.5 py-1 font-body text-[11px] border border-border disabled:opacity-40 hover:bg-muted transition-colors"
            >
              ← Anterior
            </button>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="rounded-md px-2.5 py-1 font-body text-[11px] border border-border disabled:opacity-40 hover:bg-muted transition-colors"
            >
              Siguiente →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
