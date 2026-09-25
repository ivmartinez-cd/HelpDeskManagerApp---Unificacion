import type { Page } from "@/shared/types/pagination";
import { PENDIENTE, type Incidente, type Reporte } from "../../types/reporte";
import { formatearEntero } from "../../lib/periodos";
import { colorCategoria } from "../dashboard/graficos/utilidades";
import { BORDE, ESTILO_ETIQUETA, FONDO_SUAVE, GRIS, TINTA } from "./estilos";

const CELDA = {
  padding: "6px 8px",
  borderBottom: `1px solid ${BORDE}`,
  fontSize: 10.5,
  lineHeight: 1.35,
  verticalAlign: "top",
  color: TINTA,
} as const;

const COLUMNAS = ["Número", "Fecha", "Sucursal", "Tarea realizada", "Tipificación"];

function Fila({ reporte, incidente }: { reporte: Reporte; incidente: Incidente }) {
  const categoria = incidente.categoria || PENDIENTE;
  return (
    <tr>
      <td style={{ ...CELDA, whiteSpace: "nowrap", fontWeight: 700 }}>{incidente.numero}</td>
      <td style={{ ...CELDA, whiteSpace: "nowrap" }}>{incidente.fecha}</td>
      <td style={CELDA}>{incidente.sucursal || "—"}</td>
      <td style={{ ...CELDA, color: GRIS }}>{incidente.solucion || "—"}</td>
      <td style={CELDA}>
        <span style={{ fontWeight: 700, color: colorCategoria(reporte, categoria) }}>{categoria}</span>
        {incidente.subcategoria && <span style={{ color: GRIS }}> › {incidente.subcategoria.trim()}</span>}
      </td>
    </tr>
  );
}

/** "Detalle de incidentes (Top 50)": los primeros 50 en el orden del reporte,
 * en página nueva. */
export function DetalleImprimible({ reporte, incidentes }: { reporte: Reporte; incidentes: Page<Incidente> }) {
  return (
    <section className="ri-salto">
      <h2 style={{ margin: "0 0 10px", fontSize: 17, fontWeight: 800, color: TINTA }}>Detalle de incidentes (Top 50)</h2>
      <table style={{ width: "100%", borderCollapse: "collapse", tableLayout: "fixed" }}>
        <colgroup>
          <col style={{ width: "11%" }} />
          <col style={{ width: "11%" }} />
          <col style={{ width: "19%" }} />
          <col style={{ width: "35%" }} />
          <col style={{ width: "24%" }} />
        </colgroup>
        <thead>
          <tr>
            {COLUMNAS.map((c) => (
              <th
                key={c}
                style={{ ...ESTILO_ETIQUETA, textAlign: "left", padding: "7px 8px", background: FONDO_SUAVE, borderBottom: `2px solid ${BORDE}` }}
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {incidentes.items.length === 0 ? (
            <tr>
              <td colSpan={COLUMNAS.length} style={{ ...CELDA, textAlign: "center", padding: 16 }}>
                Sin incidentes en el período
              </td>
            </tr>
          ) : (
            incidentes.items.map((i) => <Fila key={i.id} reporte={reporte} incidente={i} />)
          )}
        </tbody>
      </table>
      {incidentes.total > incidentes.items.length && (
        <p style={{ margin: "8px 0 0", fontSize: 10.5, fontStyle: "italic", color: GRIS }}>
          * Mostrando los primeros {formatearEntero(incidentes.items.length)} incidentes de un total de{" "}
          {formatearEntero(incidentes.total)} para el período.
        </p>
      )}
    </section>
  );
}
