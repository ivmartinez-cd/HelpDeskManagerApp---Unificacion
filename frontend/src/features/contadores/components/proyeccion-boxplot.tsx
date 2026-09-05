import type { BoxplotParque } from "../types/proyeccion";

/** Boxplot del parque de referencia (panel de candidatos) — sin librería:
 * no hay un componente equivalente en el resto de la app ni un plugin de
 * boxplot ya instalado, así que se arma con SVG plano y los tokens de color
 * existentes (`--info`, `--accent`). Ver mockup aprobado. */

const ANCHO = 340;
const ALTO = 64;
const EJE_Y = 30;

interface ProyeccionBoxplotProps {
  data: BoxplotParque;
}

function escala(valor: number, min: number, max: number): number {
  if (max <= min) return ANCHO / 2;
  return 8 + ((valor - min) / (max - min)) * (ANCHO - 16);
}

export function ProyeccionBoxplot({ data }: ProyeccionBoxplotProps) {
  const { minimo, q1, mediana, q3, maximo, valor_equipo } = data;
  const x = (v: number) => escala(v, minimo, maximo);

  return (
    <svg
      viewBox={`0 0 ${ANCHO} ${ALTO}`}
      width="100%"
      height={ALTO}
      role="img"
      aria-label="Distribución del parque de referencia"
    >
      <line x1={0} y1={EJE_Y} x2={ANCHO} y2={EJE_Y} stroke="var(--border)" strokeWidth={1} />
      <line x1={x(minimo)} y1={26} x2={x(minimo)} y2={34} stroke="var(--muted-foreground)" />
      <line x1={x(maximo)} y1={26} x2={x(maximo)} y2={34} stroke="var(--muted-foreground)" />
      <line x1={x(minimo)} y1={30} x2={x(q1)} y2={30} stroke="var(--muted-foreground)" strokeDasharray="2,2" />
      <line x1={x(q3)} y1={30} x2={x(maximo)} y2={30} stroke="var(--muted-foreground)" strokeDasharray="2,2" />
      <rect
        x={x(q1)}
        y={16}
        width={Math.max(x(q3) - x(q1), 1)}
        height={28}
        fill="var(--info)"
        fillOpacity={0.25}
        stroke="var(--info)"
        strokeWidth={1.5}
        rx={3}
      />
      <line x1={x(mediana)} y1={16} x2={x(mediana)} y2={44} stroke="var(--info)" strokeWidth={2} />
      <line x1={x(valor_equipo)} y1={8} x2={x(valor_equipo)} y2={52} stroke="var(--accent)" strokeWidth={2} />
      <text x={x(valor_equipo)} y={6} textAnchor="middle" fontSize={9.5} fontWeight={700} fill="var(--accent)">
        este equipo
      </text>
    </svg>
  );
}
