export function ReportAiSummary({ summary }: { summary: string | null }) {
  if (!summary) return null;
  return (
    <div
      style={{
        marginBottom: 20, padding: 12, borderRadius: 8,
        border: "1px solid #F7941D55", backgroundColor: "#F7941D0d",
      }}
    >
      <h2 style={{ fontSize: 13, fontWeight: 800, color: "#111", marginBottom: 6 }}>
        Diagnóstico con IA
      </h2>
      <p style={{ fontSize: 11, lineHeight: 1.5, color: "#222", whiteSpace: "pre-wrap", margin: 0 }}>
        {summary}
      </p>
    </div>
  );
}
