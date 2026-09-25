import type { Reporte } from "../../types/reporte";
import { formatearEntero } from "../../lib/periodos";
import { BORDE, ESTILO_ETIQUETA, GRIS, NARANJA, TINTA } from "./estilos";

/** Encabezado del PDF: título, cliente, rango, cantidad de meses, fecha de
 * generación y el logo de Canal Directo (el mismo `/logo.svg` naranja del
 * sidebar: se ve bien sobre blanco). */
export function EncabezadoImprimible({ reporte, generadoEn }: { reporte: Reporte; generadoEn: string }) {
  const generado = new Date(generadoEn).toLocaleDateString("es-AR");
  return (
    <header
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-end",
        gap: 24,
        paddingBottom: 14,
        marginBottom: 20,
        borderBottom: "3px solid transparent",
        borderImage: `linear-gradient(to right, ${NARANJA} 0%, ${NARANJA} 65%, ${GRIS} 65%, ${GRIS} 100%) 1`,
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <h1 style={{ margin: 0, fontSize: 26, fontWeight: 800, lineHeight: 1.1, color: TINTA }}>
          Reporte de Incidentes
        </h1>
        <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: GRIS }}>{reporte.empresa.nombre}</h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, fontSize: 12, color: GRIS }}>
          <span>
            Período: <strong style={{ color: TINTA }}>{reporte.rango_etiqueta}</strong>
          </span>
          {reporte.meses > 1 && <span>· {reporte.meses} meses</span>}
          <span>· Generado {generado}</span>
        </div>
      </div>
      {/* eslint-disable-next-line @next/next/no-img-element -- SVG de marca; <img> plano para que el popup lo pinte sin loader */}
      <img src="/logo.svg" alt="Canal Directo" style={{ height: 34, width: "auto" }} />
    </header>
  );
}

function Kpi({ etiqueta, valor, pista, destacado }: { etiqueta: string; valor: string; pista: string; destacado?: boolean }) {
  return (
    <div
      className="ri-bloque"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 4,
        padding: "12px 14px",
        border: `1px solid ${BORDE}`,
        borderTop: `3px solid ${destacado ? NARANJA : GRIS}`,
        borderRadius: 10,
        minWidth: 0,
      }}
    >
      <span style={ESTILO_ETIQUETA}>{etiqueta}</span>
      <span style={{ fontSize: 20, fontWeight: 800, color: destacado ? NARANJA : TINTA, overflowWrap: "anywhere" }}>
        {valor}
      </span>
      <span style={{ fontSize: 11, color: GRIS }}>{pista}</span>
    </div>
  );
}

/** Los 3 KPIs, con la misma redacción que `KpisReporte`. */
export function KpisImprimibles({ reporte }: { reporte: Reporte }) {
  const { kpis } = reporte;
  const hayCasos = kpis.total > 0;
  return (
    <section style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 12, marginBottom: 16 }}>
      <Kpi
        etiqueta="Total incidentes"
        valor={formatearEntero(kpis.total)}
        pista={`en ${reporte.rango_etiqueta}`}
        destacado
      />
      <Kpi
        etiqueta="Categoría principal"
        valor={kpis.categoria_principal}
        pista={
          hayCasos
            ? `${formatearEntero(kpis.categoria_principal_cantidad)} casos (${kpis.categoria_principal_pct}%)`
            : "Sin incidentes"
        }
      />
      <Kpi
        etiqueta="Sucursal principal"
        valor={kpis.sucursal_principal}
        pista={hayCasos ? `${formatearEntero(kpis.sucursal_principal_cantidad)} incidentes` : "Sin incidentes"}
      />
    </section>
  );
}
