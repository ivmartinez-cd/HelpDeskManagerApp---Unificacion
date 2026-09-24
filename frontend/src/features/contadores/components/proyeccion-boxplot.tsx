import type { BoxplotParque } from "../types/proyeccion";
import { n0, redondeoBancario } from "./proyeccion-formato";

/** Boxplot del parque del cliente en el panel de candidatos — puerto de
 * `CalcularBoxplotData` / `RenderBoxplot` de `PanelCandidatos.razor` (v1.7):
 * caja Q1–Q3, línea del promedio del parque, bigotes de Tukey (Q1±1.5·IQR,
 * piso 0) y el punto "este equipo" en la estimación vigente (la vista
 * previa de la P/L si hay una; si no, las impresiones de la fila). */

const W = 290;
const H = 90;
const BAR_Y = 32;
const BAR_H = 18;
const MARGEN = 12;
const USABLE = W - MARGEN * 2;
const MID_Y = BAR_Y + Math.floor(BAR_H / 2);
const TICK_H = 6;
const LBL_Y = H - 4;

interface Escala {
  lo: number;
  hi: number;
  wlo: number | null;
  whi: number | null;
}

function escala({ q1, q3, mediana: prom }: BoxplotParque, estim: number | null): Escala | null {
  let wlo: number | null = null;
  let whi: number | null = null;
  if (q1 !== null && q3 !== null) {
    wlo = Math.max(0, q1 - 1.5 * (q3 - q1));
    whi = q3 + 1.5 * (q3 - q1);
  }
  const lo = Math.max(0, Math.min(wlo ?? q1 ?? prom * 0.6, estim ?? prom) * 0.85);
  const hi = Math.max(whi ?? q3 ?? prom * 1.4, estim ?? prom) * 1.15;
  return hi <= lo ? null : { lo, hi, wlo, whi };
}

function descripcion(q1: number | null, q3: number | null, estim: number | null, conBigotes: boolean): string | null {
  if (estim === null) return null;
  const dentro = q1 !== null && q3 !== null && estim >= q1 && estim <= q3;
  return `Estimación ${n0(estim)} págs cae ${dentro ? "dentro" : "fuera"} del rango sano del parque (Q1–Q3).${
    conBigotes ? " Sin descartes IQR aplicados." : ""
  }`;
}

interface ProyeccionBoxplotProps {
  data: BoxplotParque;
  estimacion: number | null;
  // Encabezado de la sección: no se muestra si no hay gráfico que dibujar.
  titulo: React.ReactNode;
}

export function ProyeccionBoxplot({ data, estimacion, titulo }: ProyeccionBoxplotProps) {
  const e = escala(data, estimacion);
  if (e === null || data.mediana <= 0) return null;
  const { q1, q3, mediana: prom, n_equipos } = data;
  const x = (v: number) => MARGEN + redondeoBancario(((v - e.lo) / (e.hi - e.lo)) * USABLE);
  const xQ1 = q1 !== null ? x(q1) : MARGEN + Math.floor(USABLE / 4);
  const xQ3 = q3 !== null ? x(q3) : MARGEN + Math.floor((USABLE * 3) / 4);
  const xProm = x(prom);
  const xWLo = e.wlo !== null ? x(e.wlo) : MARGEN;
  const xWHi = e.whi !== null ? x(e.whi) : W - MARGEN;
  // Como `RenderBoxplot`: fuera por la izquierda (x < 0, p. ej. un negativo
  // conservado entre reales) no se dibuja; si no, se recorta a [6, W−6].
  const xCrudo = estimacion !== null ? x(estimacion) : -1;
  const xEstim = xCrudo >= 0 ? Math.min(Math.max(xCrudo, 6), W - 6) : null;
  const desc = descripcion(q1, q3, estimacion, e.wlo !== null || e.whi !== null);
  const etiqueta = (vx: number, texto: string, anchor: "start" | "middle" | "end") => (
    <text x={vx} y={LBL_Y} textAnchor={anchor} fontSize={8.5} fill="var(--muted-foreground)">
      {texto}
    </text>
  );

  return (
    <div>
      {titulo}
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} role="img" aria-label="Distribución del parque del cliente">
        <line x1={xWLo} y1={MID_Y} x2={xQ1} y2={MID_Y} stroke="var(--muted-foreground)" strokeDasharray="2,2" />
        <line x1={xQ3} y1={MID_Y} x2={xWHi} y2={MID_Y} stroke="var(--muted-foreground)" strokeDasharray="2,2" />
        <line x1={xWLo} y1={MID_Y - TICK_H} x2={xWLo} y2={MID_Y + TICK_H} stroke="var(--muted-foreground)" />
        <line x1={xWHi} y1={MID_Y - TICK_H} x2={xWHi} y2={MID_Y + TICK_H} stroke="var(--muted-foreground)" />
        <rect x={xQ1} y={BAR_Y} width={Math.max(1, xQ3 - xQ1)} height={BAR_H} fill="var(--info)" fillOpacity={0.25}
          stroke="var(--info)" strokeWidth={1.5} rx={3} />
        <line x1={xProm} y1={BAR_Y} x2={xProm} y2={BAR_Y + BAR_H} stroke="var(--info)" strokeWidth={2} />
        {xEstim !== null && (
          <>
            <text x={xEstim} y={BAR_Y - 6} textAnchor="middle" fontSize={9.5} fontWeight={700} fill="var(--accent)">
              este equipo
            </text>
            <circle cx={xEstim} cy={MID_Y} r={5} fill="var(--accent)" />
          </>
        )}
        {n_equipos > 0 && (
          <text x={W - 2} y={10} textAnchor="end" fontSize={9} fill="var(--muted-foreground)">
            n={n_equipos}
          </text>
        )}
        {e.wlo !== null && etiqueta(xWLo, n0(e.wlo), "start")}
        {q1 !== null && etiqueta(xQ1, `Q1 ${n0(q1)}`, "middle")}
        {etiqueta(xProm, `x̄ ${n0(prom)}`, "middle")}
        {q3 !== null && etiqueta(xQ3, `Q3 ${n0(q3)}`, "middle")}
        {e.whi !== null && etiqueta(xWHi, n0(e.whi), "end")}
      </svg>
      {desc && <p className="mt-1 text-[11px] text-muted-foreground">{desc}</p>}
    </div>
  );
}
