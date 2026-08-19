import { SEV_COLOR } from "../../utils/analysis-utils";
import type { Severity } from "../../types/analisis-log-hp";

interface Props {
  serial: string;
  modelName: string;
  globalSeverity: Severity;
  generatedAtIso: string;
}

export function ReportHeader({ serial, modelName, globalSeverity, generatedAtIso }: Props) {
  const generated = new Date(generatedAtIso).toLocaleString("es-AR", {
    day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
  return (
    <div style={{ borderBottom: "3px solid #F7941D", paddingBottom: 16, marginBottom: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 700, letterSpacing: "0.08em", color: "#58595B" }}>
            CANAL DIRECTO
          </div>
          <h1 style={{ fontSize: 22, fontWeight: 800, margin: "4px 0 0", color: "#111" }}>
            Reporte Ejecutivo — HP Logs Analyzer
          </h1>
        </div>
        <div
          style={{
            fontSize: 11, fontWeight: 700, textTransform: "uppercase",
            padding: "4px 10px", borderRadius: 999,
            color: "#fff", backgroundColor: SEV_COLOR[globalSeverity],
          }}
        >
          {globalSeverity}
        </div>
      </div>
      <div style={{ marginTop: 12, fontSize: 12, color: "#444", display: "flex", gap: 24 }}>
        <span><strong>Equipo:</strong> {modelName}</span>
        <span><strong>Serie:</strong> {serial}</span>
        <span><strong>Generado:</strong> {generated}</span>
      </div>
    </div>
  );
}
