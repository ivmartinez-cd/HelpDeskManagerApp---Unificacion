import { redondeoBancario } from "./proyeccion-formato";

/** Mini gráfico "12 meses" de la grilla — puerto de `BarChart.razor` (v1.7):
 * 11 barras de historia (H11 → H01, viejo → reciente) + la del período
 * (las impresiones de la fila, real o estimada) con una línea punteada a su
 * altura. Si el período supera en más de 5% el máximo histórico, "↑ valor"
 * arriba a la derecha; sin historia ni estimado, "sin historia". */

const ANCHO = 120;
const ALTO = 32;
const BASE = 28;
const ALTURA_MAX = 26;
const MESES_HISTORIA = 11;

const formatoK = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 1 });
const formatoN0 = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 0 });

/** `FK` del legacy: "12,3k" desde mil, entero con separador debajo. */
function fk(v: number): string {
  return v >= 1000 ? `${formatoK.format(v / 1000)}k` : formatoN0.format(v);
}

interface ProyeccionSparklineProps {
  historico12: number[];
  impresiones: number | null;
  prom6: number | null;
}

export function ProyeccionSparkline({ historico12, impresiones, prom6 }: ProyeccionSparklineProps) {
  const historico = historico12.slice(0, MESES_HISTORIA);
  const tieneHistorico = historico.length > 0;
  const valorMes = (i: number) => (tieneHistorico ? (historico[i] ?? 0) : (prom6 ?? 0));
  const maxRef = tieneHistorico ? Math.max(...historico) : (prom6 ?? 0);
  const imp = impresiones ?? 0;
  const techo = Math.max(maxRef, imp) * 1.1;
  const altura = (v: number) =>
    techo <= 0 || v <= 0 ? 0 : Math.min(Math.max(redondeoBancario((v / techo) * ALTURA_MAX), 1), ALTURA_MAX);
  const alturaEstim = altura(imp);
  const lineaY = BASE - Math.max(alturaEstim, 1);
  const desborda = tieneHistorico && maxRef > 0 && imp > maxRef * 1.05;
  const sinHistoria = !tieneHistorico && (prom6 ?? 0) <= 0 && imp <= 0;

  return (
    <svg width={ANCHO} height={ALTO} viewBox={`0 0 ${ANCHO} ${ALTO}`} className="block" aria-hidden>
      <line x1={0} y1={BASE} x2={ANCHO} y2={BASE} stroke="var(--border)" strokeWidth={0.5} />
      {Array.from({ length: MESES_HISTORIA }, (_, i) => (
        <Barra key={i} x={i * 10} alto={altura(valorMes(i))} color="var(--info)" opacidad={0.85} />
      ))}
      <Barra x={110} alto={alturaEstim} color="var(--destructive)" opacidad={0.55} />
      <line x1={0} y1={lineaY} x2={ANCHO} y2={lineaY} stroke="var(--destructive)" strokeWidth={1.1} strokeDasharray="2,2" />
      {desborda && (
        <text x={118} y={9} textAnchor="end" fontSize={9} fontWeight={700} fill="var(--destructive)">
          ↑ {fk(imp)}
        </text>
      )}
      {sinHistoria && (
        <text x={55} y={14} textAnchor="middle" fontSize={9} fill="var(--muted-foreground)">
          sin historia
        </text>
      )}
    </svg>
  );
}

function Barra({ x, alto, color, opacidad }: { x: number; alto: number; color: string; opacidad: number }) {
  if (alto <= 0) return <rect x={x} y={BASE - 2} width={7} height={2} fill="var(--muted)" />;
  return <rect x={x} y={BASE - alto} width={7} height={alto} fill={color} opacity={opacidad} />;
}
