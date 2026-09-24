"use client";

import { useMemo, useState } from "react";
import type { HistorialLectura } from "../types/proyeccion";

/** Combo-chart SVG (línea de contador + barras de impresiones por período) —
 * puerto de `DrillDownModal.razor.cs::BuildSvgContent` del legacy: mismo
 * viewBox y constantes de layout, para que la lectura visual sea idéntica.
 * Sin librería de charts: es un solo SVG hecho a mano, más simple de portar
 * 1:1 que forzar un combo de ejes duales en chart.js. */

const VIEW_W = 860;
const VIEW_H = 300;
const X_MIN = 60;
const X_MAX = 820;
const Y_LINE_MIN = 15;
const Y_LINE_MAX = 155;
const Y_SEP = 162;
const Y_BAR_TOP = 168;
const Y_BAR_BASE = 248;
const Y_AXIS_X = 263;

// `TipoToma.Reales` e iniciales/finales/reinicio del legacy.
const TIPOS_REALES = new Set([1, 2, 3, 6, 7, 9, 10, 12, 15, 17, 20, 21, 22, 23]);
const INICIALES_FINALES = new Set([8, 13, 16]);

export const esTipoReal = (t: number) => TIPOS_REALES.has(t);
export const esInicialFinal = (t: number) => INICIALES_FINALES.has(t);

/** Orden cronológico del legacy (fecha y, a igual fecha, ID_Contador): la
 * API las devuelve de la más nueva a la más vieja, así que se invierten
 * antes del orden estable por fecha. */
export function ordenCronologico(lecturas: HistorialLectura[]): HistorialLectura[] {
  return [...lecturas].reverse().sort((a, b) => a.fecha.localeCompare(b.fecha));
}

export function colorPunto(idTipoToma: number): string {
  if (idTipoToma === 4) return "#ca8a04";
  if (idTipoToma === 14 || idTipoToma === 19) return "#ea580c";
  if (INICIALES_FINALES.has(idTipoToma)) return "#2563eb";
  if (TIPOS_REALES.has(idTipoToma)) return "#16a34a";
  return "#6b7280";
}

function formatImp(v: number): string {
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1000) return `${(v / 1000).toFixed(0)}k`;
  return v.toFixed(0);
}

const numberFormat = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 0 });
// Siempre en UTC: las fechas son días sin hora (UTC 00:00); en hora local
// (UTC−3) un día 1 caería en el mes anterior.
const mesFormat = new Intl.DateTimeFormat("es-AR", { month: "short", year: "2-digit", timeZone: "UTC" });
const DIA_MS = 86_400_000;

interface Hover {
  left: number;
  top: number;
  contenido: React.ReactNode;
}

function useEscalas(asc: HistorialLectura[]) {
  return useMemo(() => {
    // Fechas como instantes UTC 00:00 (`DateOnly` del legacy): todas las
    // lecturas del mismo día → fechaMax = fechaMin + 1 día.
    const fechaMin = asc.length > 0 ? Date.parse(asc[0].fecha) : 0;
    const ultima = asc.length > 0 ? Date.parse(asc[asc.length - 1].fecha) : 0;
    const fechaMax = ultima === fechaMin ? fechaMin + DIA_MS : ultima;
    const x = (fecha: string) => X_MIN + ((Date.parse(fecha) - fechaMin) / (fechaMax - fechaMin)) * (X_MAX - X_MIN);

    const valores = asc.map((l) => l.valor);
    let valMin = Math.min(...valores);
    let valMax = Math.max(...valores);
    if (valMin === valMax) {
      valMin -= 1000;
      valMax += 1000;
    }
    const pad = (valMax - valMin) * 0.08;
    valMin -= pad;
    valMax += pad;
    const y = (valor: number) => Y_LINE_MAX - ((valor - valMin) / (valMax - valMin)) * (Y_LINE_MAX - Y_LINE_MIN);

    const periodosFC = asc.filter((l) => l.es_fc);
    const impMax = Math.max(1, ...periodosFC.map((l) => l.fc_impresiones ?? 0).filter((v) => v > 0));
    const alturaBarra = (imp: number) => (imp / impMax) * (Y_BAR_BASE - Y_BAR_TOP);

    return { x, y, valMin, valMax, periodosFC, impMax, alturaBarra, fechaMin, fechaMax };
  }, [asc]);
}

export function HistorialChart({ lecturas }: { lecturas: HistorialLectura[] }) {
  const asc = useMemo(() => ordenCronologico(lecturas), [lecturas]);
  const [hover, setHover] = useState<Hover | null>(null);
  const escalas = useEscalas(asc);

  if (asc.length === 0) return <p className="text-sm text-muted-foreground">Sin lecturas en el período.</p>;

  const puntos = asc.map((l) => ({ lectura: l, cx: escalas.x(l.fecha), cy: escalas.y(l.valor) }));
  const polyPts = puntos.map((p) => `${p.cx.toFixed(1)},${p.cy.toFixed(1)}`).join(" ");
  const areaPts = `${polyPts} ${puntos.at(-1)!.cx.toFixed(1)},${Y_LINE_MAX} ${puntos[0].cx.toFixed(1)},${Y_LINE_MAX}`;
  const barW = Math.min(22, ((X_MAX - X_MIN) / Math.max(escalas.periodosFC.length, 1)) * 0.6);

  const mostrarTooltip = (
    e: React.MouseEvent<SVGCircleElement | SVGRectElement>,
    cx: number,
    cy: number,
    contenido: React.ReactNode,
  ) => {
    const rect = e.currentTarget.ownerSVGElement?.getBoundingClientRect();
    if (!rect) return;
    setHover({ left: (cx / VIEW_W) * rect.width, top: (cy / VIEW_H) * rect.height, contenido });
  };

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${VIEW_W} ${VIEW_H}`} className="w-full" onMouseLeave={() => setHover(null)}>
        {[0, 1, 2, 3, 4].map((i) => {
          const y = Y_LINE_MIN + (i * (Y_LINE_MAX - Y_LINE_MIN)) / 4;
          const label = escalas.valMax - ((escalas.valMax - escalas.valMin) * i) / 4;
          return (
            <g key={i}>
              <line x1={X_MIN} y1={y} x2={X_MAX} y2={y} stroke="#e5e7eb" strokeWidth={1} />
              <text x={X_MIN - 4} y={y + 3} textAnchor="end" fontSize={9} fill="#9ca3af">
                {formatImp(label)}
              </text>
            </g>
          );
        })}

        <polygon fill="#2563eb" fillOpacity={0.08} points={areaPts} />
        <polyline fill="none" stroke="#2563eb" strokeWidth={2} strokeLinejoin="round" points={polyPts} />

        {puntos.map((p, i) => (
          <g key={i}>
            {p.lectura.es_fc && <circle cx={p.cx} cy={p.cy} r={9} fill="none" stroke="#1d4ed8" strokeWidth={2} />}
            <circle
              cx={p.cx}
              cy={p.cy}
              r={esTipoReal(p.lectura.id_tipo_toma) || esInicialFinal(p.lectura.id_tipo_toma) ? 5 : 4}
              fill={colorPunto(p.lectura.id_tipo_toma)}
              stroke="#fff"
              strokeWidth={2}
              className="cursor-pointer"
              onMouseEnter={(e) => mostrarTooltip(e, p.cx, p.cy, <PuntoTooltip lectura={p.lectura} />)}
            />
          </g>
        ))}

        <line x1={X_MIN} y1={Y_SEP} x2={X_MAX} y2={Y_SEP} stroke="#d1d5db" strokeWidth={1} />
        <text x={X_MIN} y={Y_SEP + 13} fontSize={9} fill="#9ca3af" fontWeight={600}>
          IMP / PERÍODO
        </text>

        {[0, 1, 2].map((i) => (
          <line
            key={i}
            x1={X_MIN}
            y1={Y_BAR_TOP + (i * (Y_BAR_BASE - Y_BAR_TOP)) / 2}
            x2={X_MAX}
            y2={Y_BAR_TOP + (i * (Y_BAR_BASE - Y_BAR_TOP)) / 2}
            stroke={i < 2 ? "#f3f4f6" : "#e5e7eb"}
            strokeWidth={1}
          />
        ))}
        <text x={X_MAX + 5} y={Y_BAR_TOP + 4} fontSize={9} fill="#9ca3af">
          {formatImp(escalas.impMax)}
        </text>
        <text x={X_MAX + 5} y={Y_BAR_BASE} fontSize={9} fill="#9ca3af">
          0
        </text>

        {escalas.periodosFC.map((l, i) => {
          const cx = escalas.x(l.fecha);
          const imp = l.fc_impresiones ?? 0;
          const h = escalas.alturaBarra(imp);
          return (
            <rect
              key={i}
              x={cx - barW / 2}
              y={h < 1 ? Y_BAR_BASE - 3 : Y_BAR_BASE - h}
              width={barW}
              height={h < 1 ? 3 : h}
              rx={h < 1 ? 1 : 2}
              fill={colorPunto(l.id_tipo_toma)}
              opacity={h < 1 ? 0.35 : 0.75}
              className="cursor-pointer"
              onMouseEnter={(e) => mostrarTooltip(e, cx, Y_BAR_TOP, <BarraTooltip lectura={l} />)}
            />
          );
        })}

        <line x1={X_MIN} y1={Y_BAR_BASE} x2={X_MAX} y2={Y_BAR_BASE} stroke="#d1d5db" strokeWidth={1} />
        {mesesEtiqueta(escalas.fechaMin, escalas.fechaMax).map(({ x, label }, i) => (
          <text key={i} x={x} y={Y_AXIS_X} fontSize={9} fill="#9ca3af" textAnchor="middle">
            {label}
          </text>
        ))}
      </svg>

      {hover && (
        <div
          className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full rounded-[8px] border border-border bg-card px-3 py-2 text-xs shadow-lg"
          style={{ left: hover.left, top: hover.top - 10 }}
        >
          {hover.contenido}
        </div>
      )}
    </div>
  );
}

function mesesEtiqueta(fechaMinMs: number, fechaMaxMs: number): { x: number; label: string }[] {
  const min = new Date(fechaMinMs);
  const max = new Date(fechaMaxMs);
  const mesesRango = Math.round((fechaMaxMs - fechaMinMs) / (DIA_MS * 30.44));
  const paso = mesesRango > 15 ? 3 : mesesRango > 8 ? 2 : 1;
  const etiquetas: { x: number; label: string }[] = [];
  // `EnumerarMeses`: del 1° del mes de fechaMin al 1° del mes de fechaMax.
  let cursor = Date.UTC(min.getUTCFullYear(), min.getUTCMonth(), 1);
  const fin = Date.UTC(max.getUTCFullYear(), max.getUTCMonth(), 1);
  while (cursor <= fin) {
    const d = new Date(cursor);
    if (d.getUTCMonth() % paso === 0) {
      const x = X_MIN + ((cursor - fechaMinMs) / (fechaMaxMs - fechaMinMs)) * (X_MAX - X_MIN);
      if (x >= X_MIN && x <= X_MAX) etiquetas.push({ x, label: mesFormat.format(d) });
    }
    cursor = Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1);
  }
  return etiquetas;
}

function PuntoTooltip({ lectura }: { lectura: HistorialLectura }) {
  return (
    <div className="min-w-[140px]">
      <p className="text-muted-foreground">{lectura.fecha.split("-").reverse().join("/")}</p>
      <p style={{ color: colorPunto(lectura.id_tipo_toma) }}>
        T{lectura.id_tipo_toma} · {lectura.tipo_toma_desc}
      </p>
      <p className="font-bold tabular-nums">{numberFormat.format(lectura.valor)}</p>
      {lectura.delta !== null && (
        <p className="text-muted-foreground">
          Δ {lectura.delta >= 0 ? "+" : ""}
          {numberFormat.format(lectura.delta)} imp.
        </p>
      )}
      <PuntoBadge lectura={lectura} />
    </div>
  );
}

function PuntoBadge({ lectura }: { lectura: HistorialLectura }) {
  const clase = "mt-1 inline-block rounded-full px-2 py-0.5 text-[10px] font-bold";
  if (lectura.es_fc) return <span className={`${clase} bg-info/20 text-info`}>✓ Usado en facturación</span>;
  if (lectura.id_tipo_toma === 4 && !lectura.para_facturar) {
    return <span className={`${clase} bg-warning/20 text-warning`}>⚠ PF = 0, no facturado</span>;
  }
  if (esInicialFinal(lectura.id_tipo_toma)) {
    return <span className={`${clase} bg-info/10 text-info`}>{validacionHistorial(lectura)}</span>;
  }
  return null;
}

/** `ValidacionLabel` de `HistorialLectura` (v1.7). */
export function validacionHistorial(l: HistorialLectura): string {
  const t = l.id_tipo_toma;
  if (t === 14 || t === 19) return "—";
  if (t === 4) return l.para_facturar ? "T4 facturado" : "⚠ PF = 0";
  if (t === 16) return "Reinicio de contador";
  if (t === 8 || t === 13) return validacionInicialFinal(l);
  return esTipoReal(t) ? "✓ Válida" : "—";
}

function validacionInicialFinal(l: HistorialLectura): string {
  if (l.es_fc) return "✓ Válida";
  if (l.es_cambio_empresa) return "Cambio de empresa";
  if (l.es_cambio_anexo) return "Cambio de anexo";
  if (l.es_ingreso) return "Ingreso del equipo";
  if (l.es_egreso) return "Egreso del equipo";
  return l.id_tipo_toma === 8 ? "Apertura" : "Cierre";
}

const periodoFormat = new Intl.DateTimeFormat("es-AR", { month: "short", year: "numeric", timeZone: "UTC" });

function BarraTooltip({ lectura }: { lectura: HistorialLectura }) {
  const periodo =
    lectura.fc_periodo_facturacion ??
    (lectura.fc_periodo_hasta ? periodoFormat.format(new Date(`${lectura.fc_periodo_hasta}T00:00:00Z`)) : null);
  return (
    <div className="min-w-[120px]">
      {periodo && <p className="text-muted-foreground">{periodo}</p>}
      <p className="font-bold tabular-nums">
        {lectura.fc_impresiones && lectura.fc_impresiones > 0
          ? `${numberFormat.format(lectura.fc_impresiones)} impr.`
          : "Sin consumo"}
      </p>
    </div>
  );
}
