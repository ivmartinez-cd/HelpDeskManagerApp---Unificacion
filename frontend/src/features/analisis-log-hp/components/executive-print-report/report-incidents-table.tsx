import type { CSSProperties } from "react";
import type { AnalysisResult } from "../../types/analisis-log-hp";
import { SEV_COLOR, fmtDatetime, normSev } from "../../utils/analysis-utils";

const TH: CSSProperties = {
  textAlign: "left", fontSize: 10, fontWeight: 700, textTransform: "uppercase",
  color: "#888", padding: "4px 8px", borderBottom: "2px solid #ddd",
};
const TD: CSSProperties = { fontSize: 11, padding: "5px 8px", borderBottom: "1px solid #eee" };

export function ReportIncidentsTable({ analysis }: { analysis: AnalysisResult }) {
  const incidents = [...analysis.incidents].sort(
    (a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime(),
  );
  return (
    <div style={{ marginBottom: 20 }}>
      <h2 style={{ fontSize: 13, fontWeight: 800, color: "#111", marginBottom: 8 }}>
        Incidencias detectadas ({incidents.length})
      </h2>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            {["Código", "Severidad", "Ocurrencias", "Inicio", "Fin", "Descripción"].map((h) => (
              <th key={h} style={TH}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {incidents.map((inc) => {
            const sev = normSev(inc.severity);
            return (
              <tr key={inc.id}>
                <td style={{ ...TD, color: SEV_COLOR[sev], fontWeight: 700 }}>{inc.code}</td>
                <td style={{ ...TD, color: SEV_COLOR[sev] }}>{sev}</td>
                <td style={TD}>{inc.occurrences}</td>
                <td style={TD}>{fmtDatetime(inc.start_time)}</td>
                <td style={TD}>{fmtDatetime(inc.end_time)}</td>
                <td style={TD}>{inc.code_description?.slice(0, 60) ?? "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
