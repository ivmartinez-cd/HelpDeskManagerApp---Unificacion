import type { ReactNode } from "react";
import type { Reporte } from "../../types/reporte";
import { formatearEntero } from "../../lib/periodos";
import { categoriaDe, colorCategoria, formatearPct } from "../dashboard/graficos/utilidades";
import { BORDE, ESTILO_ETIQUETA, FONDO_SUAVE, GRIS, NARANJA, TINTA } from "./estilos";

interface FilaTabla {
  nombre: string;
  color: string;
  cantidad: number;
  pct: number;
  detalle?: string;
}

const CELDA = { padding: "5px 8px", borderBottom: `1px solid ${BORDE}`, fontSize: 12 } as const;
const NUMERO = { ...CELDA, textAlign: "right", fontVariantNumeric: "tabular-nums", whiteSpace: "nowrap" } as const;

function Tabla({ titulo, filas }: { titulo: string; filas: FilaTabla[] }) {
  return (
    <div style={{ marginTop: 12 }}>
      <p style={{ ...ESTILO_ETIQUETA, margin: "0 0 4px" }}>{titulo}</p>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <tbody>
          {filas.map((f) => (
            <tr key={f.nombre}>
              <td style={{ ...CELDA, color: TINTA }}>
                <span
                  style={{ display: "inline-block", width: 8, height: 8, borderRadius: 2, background: f.color, marginRight: 8 }}
                />
                {f.nombre}
                {f.detalle && <span style={{ marginLeft: 8, fontSize: 10, color: GRIS }}>{f.detalle}</span>}
              </td>
              <td style={{ ...NUMERO, fontWeight: 700, color: TINTA, width: 60 }}>{formatearEntero(f.cantidad)}</td>
              <td style={{ ...NUMERO, color: GRIS, width: 60 }}>{formatearPct(f.pct)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Titular({ children, cifra }: { children: ReactNode; cifra: string }) {
  return (
    <div style={{ display: "flex", gap: 16, alignItems: "center", padding: 14, background: FONDO_SUAVE, borderRadius: 10 }}>
      <span style={{ fontSize: 36, fontWeight: 800, lineHeight: 1, color: NARANJA }}>{cifra}</span>
      <div>{children}</div>
    </div>
  );
}

/** "Oportunidades de Mejora" en versión papel: mismos datos y redacción que
 * `OportunidadesMejora`, como tablas (sin filtros ni botones). */
export function OportunidadesImprimible({ reporte }: { reporte: Reporte }) {
  const op = reporte.oportunidades;
  if (op.fuera_del_equipo_total === 0) return null;
  return (
    <section
      className="ri-bloque"
      style={{ border: `1px solid ${BORDE}`, borderRadius: 12, padding: "14px 16px", marginBottom: 16 }}
    >
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12, marginBottom: 10 }}>
        <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: TINTA }}>Oportunidades de Mejora</h3>
        <span style={{ fontSize: 12, color: GRIS }}>
          <strong style={{ color: TINTA }}>{formatearEntero(op.fuera_del_equipo_total)}</strong> de{" "}
          {formatearEntero(op.total)} incidentes ({formatearPct(op.fuera_del_equipo_pct)}) fuera del equipo
        </span>
      </header>

      {op.sin_reparacion_total > 0 && (
        <Titular cifra={formatearEntero(op.sin_reparacion_total)}>
          <p style={{ margin: 0, fontSize: 14, fontWeight: 700, color: TINTA }}>casos se cerraron sin reparar el equipo</p>
          <p style={{ margin: "4px 0 0", fontSize: 12, lineHeight: 1.45, color: GRIS }}>
            El {formatearPct(op.sin_reparacion_pct)} de los {formatearEntero(op.total)} incidentes del período. La
            impresora estaba operativa: no se encontró falla, se resolvió con un instructivo o el problema estaba en la
            PC del puesto.
          </p>
        </Titular>
      )}

      {op.sin_reparacion_items.length > 0 && (
        <Tabla
          titulo="Por motivo"
          filas={op.sin_reparacion_items.map((i) => ({
            nombre: i.subcategoria,
            color: colorCategoria(reporte, categoriaDe(reporte, i.subcategoria)),
            cantidad: i.cantidad,
            pct: i.pct,
          }))}
        />
      )}

      {op.items.length > 0 && (
        <Tabla
          titulo="Otras causas fuera del equipo"
          filas={op.items.map((i) => ({
            nombre: i.subcategoria,
            color: colorCategoria(reporte, i.categoria),
            cantidad: i.cantidad,
            pct: i.pct,
            detalle: i.concentrado
              ? `Concentrado: ${i.sucursal_principal} · ${formatearPct(i.sucursal_principal_pct)}`
              : undefined,
          }))}
        />
      )}
    </section>
  );
}
