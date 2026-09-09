import type { BoxplotParque } from "../types/proyeccion";

/** Boxplot del parque de referencia (panel de candidatos) — sin librería:
 * no hay un componente equivalente en el resto de la app ni un plugin de
 * boxplot ya instalado, así que se arma con SVG plano y los tokens de color
 * existentes (`--info`, `--accent`). Paridad con `CalcularBoxplotData` /
 * `RenderBoxplot` de `PanelCandidatos.razor`: bigotes de Tukey (Q1±1.5·IQR)
 * calculados acá porque el backend solo expone los estadísticos crudos
 * (q1/q3/n/valor propio del equipo), no una decisión de presentación. */

const numberFormat = new Intl.NumberFormat("es-AR");

const ANCHO = 340;
const ALTO = 92;
const MARGEN_L = 10;
const MARGEN_R = 10;
const USABLE = ANCHO - MARGEN_L - MARGEN_R;
const BAR_Y = 34;
const BAR_H = 20;
const MID_Y = BAR_Y + BAR_H / 2;
const TICK_H = 7;
const LBL_Y = ALTO - 6;

interface ProyeccionBoxplotProps {
  data: BoxplotParque;
}

interface Escala {
  lo: number;
  hi: number;
  whiskerLo: number | null;
  whiskerHi: number | null;
}

function calcularEscala({ q1, q3, mediana, valor_equipo }: BoxplotParque): Escala {
  let whiskerLo: number | null = null;
  let whiskerHi: number | null = null;
  if (q1 !== null && q3 !== null) {
    const iqr = q3 - q1;
    whiskerLo = Math.max(0, q1 - 1.5 * iqr);
    whiskerHi = q3 + 1.5 * iqr;
  }
  const ancla = valor_equipo ?? mediana;
  const lo = Math.max(0, Math.min(whiskerLo ?? q1 ?? mediana * 0.6, ancla) * 0.85);
  const hiCrudo = Math.max(whiskerHi ?? q3 ?? mediana * 1.4, ancla) * 1.15;
  return { lo, hi: hiCrudo <= lo ? lo + 1 : hiCrudo, whiskerLo, whiskerHi };
}

function descripcion({ q1, q3, valor_equipo }: BoxplotParque): string | null {
  if (valor_equipo === null || q1 === null || q3 === null) return null;
  const dentro = valor_equipo >= q1 && valor_equipo <= q3;
  return (
    `Estimación ${numberFormat.format(valor_equipo)} págs cae ${dentro ? "dentro" : "fuera"} del rango sano ` +
    "del parque (Q1–Q3). Sin descartes IQR aplicados."
  );
}

export function ProyeccionBoxplot({ data }: ProyeccionBoxplotProps) {
  const { q1, q3, mediana, valor_equipo, n_equipos } = data;
  const { lo, hi, whiskerLo, whiskerHi } = calcularEscala(data);
  const x = (v: number) => MARGEN_L + ((v - lo) / (hi - lo)) * USABLE;
  const xMediana = x(mediana);
  const xEstim = valor_equipo !== null ? Math.min(Math.max(x(valor_equipo), 6), ANCHO - 6) : null;
  const desc = descripcion(data);

  return (
    <div>
      <svg
        viewBox={`0 0 ${ANCHO} ${ALTO}`}
        width="100%"
        height={ALTO}
        role="img"
        aria-label="Distribución del parque de referencia"
      >
        <line x1={0} y1={MID_Y} x2={ANCHO} y2={MID_Y} stroke="var(--border)" strokeWidth={1} />

        {q1 !== null && q3 !== null && whiskerLo !== null && whiskerHi !== null && (
          <>
            <line
              x1={x(whiskerLo)}
              y1={MID_Y}
              x2={x(q1)}
              y2={MID_Y}
              stroke="var(--muted-foreground)"
              strokeDasharray="2,2"
            />
            <line
              x1={x(q3)}
              y1={MID_Y}
              x2={x(whiskerHi)}
              y2={MID_Y}
              stroke="var(--muted-foreground)"
              strokeDasharray="2,2"
            />
            <line
              x1={x(whiskerLo)}
              y1={MID_Y - TICK_H}
              x2={x(whiskerLo)}
              y2={MID_Y + TICK_H}
              stroke="var(--muted-foreground)"
            />
            <line
              x1={x(whiskerHi)}
              y1={MID_Y - TICK_H}
              x2={x(whiskerHi)}
              y2={MID_Y + TICK_H}
              stroke="var(--muted-foreground)"
            />
            <rect
              x={x(q1)}
              y={BAR_Y}
              width={Math.max(x(q3) - x(q1), 1)}
              height={BAR_H}
              fill="var(--info)"
              fillOpacity={0.25}
              stroke="var(--info)"
              strokeWidth={1.5}
              rx={3}
            />
          </>
        )}

        <line x1={xMediana} y1={BAR_Y} x2={xMediana} y2={BAR_Y + BAR_H} stroke="var(--info)" strokeWidth={2} />

        {xEstim !== null && (
          <>
            <text x={xEstim} y={BAR_Y - 8} textAnchor="middle" fontSize={9.5} fontWeight={700} fill="var(--accent)">
              este equipo
            </text>
            <circle cx={xEstim} cy={MID_Y} r={5} fill="var(--accent)" />
          </>
        )}

        {n_equipos > 0 && (
          <text x={ANCHO - 2} y={10} textAnchor="end" fontSize={9} fill="var(--muted-foreground)">
            n={n_equipos}
          </text>
        )}

        {whiskerLo !== null && (
          <text x={x(whiskerLo)} y={LBL_Y} textAnchor="start" fontSize={8.5} fill="var(--muted-foreground)">
            {numberFormat.format(whiskerLo)}
          </text>
        )}
        {q1 !== null && (
          <text x={x(q1)} y={LBL_Y} textAnchor="middle" fontSize={8.5} fill="var(--muted-foreground)">
            Q1 {numberFormat.format(q1)}
          </text>
        )}
        <text x={xMediana} y={LBL_Y} textAnchor="middle" fontSize={8.5} fill="var(--muted-foreground)">
          prom {numberFormat.format(mediana)}
        </text>
        {q3 !== null && (
          <text x={x(q3)} y={LBL_Y} textAnchor="middle" fontSize={8.5} fill="var(--muted-foreground)">
            Q3 {numberFormat.format(q3)}
          </text>
        )}
        {whiskerHi !== null && (
          <text x={x(whiskerHi)} y={LBL_Y} textAnchor="end" fontSize={8.5} fill="var(--muted-foreground)">
            {numberFormat.format(whiskerHi)}
          </text>
        )}
      </svg>
      {desc && <p className="mt-1 text-[11px] text-muted-foreground">{desc}</p>}
    </div>
  );
}
