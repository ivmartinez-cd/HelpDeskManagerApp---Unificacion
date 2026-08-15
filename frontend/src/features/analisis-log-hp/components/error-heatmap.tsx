import type { AnalysisResult } from "../types/analisis-log-hp";
import { buildHeatmapData } from "../utils/analysis-utils";

interface Props {
  analysis: AnalysisResult;
  dateRange: string;
}

export function ErrorHeatmap({ analysis, dateRange }: Props) {
  const { matrix, days, hours, maxValue } = buildHeatmapData(analysis.events);

  function cellColor(count: number): string {
    if (count === 0) return "rgba(255,255,255,0.04)";
    const intensity = count / maxValue;
    return `rgba(239,68,68,${0.15 + intensity * 0.75})`;
  }

  const total = matrix.flat().reduce((a, b) => a + b, 0);

  return (
    <div className="rounded-[12px] border border-border bg-card p-4 flex flex-col gap-3">
      <div>
        <span className="font-heading text-[13px] font-bold text-foreground">
          Distribución temporal de fallas
        </span>
        <p className="font-body text-[11px] text-muted-foreground mt-0.5">{dateRange}</p>
      </div>

      {total === 0 ? (
        <div className="h-32 flex items-center justify-center text-muted-foreground font-body text-sm">
          Sin eventos en el período
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-separate border-spacing-[3px]" style={{ minWidth: 480 }}>
            <thead>
              <tr>
                <th className="w-10" />
                {hours.map((h) => (
                  <th key={h} className="font-body text-[10px] text-muted-foreground font-medium pb-1 text-center">
                    {String(h).padStart(2, "0")}h
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {days.map((day, di) => (
                <tr key={day}>
                  <td className="font-body text-[11px] text-muted-foreground pr-2 text-right leading-none">
                    {day}
                  </td>
                  {matrix[di].map((count, hi) => {
                    const isMax = count === maxValue && count > 0;
                    return (
                      <td key={hi} title={count > 0 ? `${count} eventos` : undefined}>
                        <div
                          className="relative h-7 w-full rounded-[4px] flex items-center justify-center"
                          style={{ backgroundColor: cellColor(count) }}
                        >
                          {isMax && (
                            <div className="h-2 w-2 rounded-full bg-white/80 absolute" />
                          )}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Leyenda */}
      <div className="flex items-center gap-2">
        <span className="font-body text-[10px] text-muted-foreground">menos</span>
        {[0, 0.25, 0.5, 0.75, 1].map((v) => (
          <div
            key={v}
            className="h-3 w-5 rounded-[3px]"
            style={{ backgroundColor: v === 0 ? "rgba(255,255,255,0.04)" : `rgba(239,68,68,${0.15 + v * 0.75})` }}
          />
        ))}
        <span className="font-body text-[10px] text-muted-foreground">más</span>
      </div>
    </div>
  );
}
