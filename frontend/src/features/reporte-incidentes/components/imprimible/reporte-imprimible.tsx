"use client";

import { useEffect } from "react";
import type { Page } from "@/shared/types/pagination";
import type { Incidente, Reporte } from "../../types/reporte";
import { GraficoCategorias } from "../dashboard/graficos/grafico-categorias";
import { GraficoEvolucion } from "../dashboard/graficos/grafico-evolucion";
import { GraficoSubcategorias } from "../dashboard/graficos/grafico-subcategorias";
import { GraficoSucursales } from "../dashboard/graficos/grafico-sucursales";
import { DetalleImprimible } from "./detalle-imprimible";
import { EncabezadoImprimible, KpisImprimibles } from "./encabezado-imprimible";
import { CSS_IMPRESION, ESTILO_RAIZ, GRIS, BORDE } from "./estilos";
import { OportunidadesImprimible } from "./oportunidades-imprimible";

export interface DatosImprimible {
  reporte: Reporte;
  incidentes: Page<Incidente>;
  generadoEn: string;
}

interface Props extends DatosImprimible {
  /** Se llama una vez montado: los efectos de los hijos (Chart.js crea y, sin
   * animación, dibuja el canvas en el suyo) ya corrieron. */
  onListo: () => void;
}

const SECCION = { marginBottom: 16 } as const;

/** Reporte ejecutivo A4 (port de `/dashboard/print` del legacy): período
 * completo, sin los filtros interactivos. Se monta oculto solo mientras se
 * exporta; el hook compartido copia su HTML (canvas → imagen) a un popup. */
export function ReporteImprimible({ reporte, incidentes, generadoEn, onListo }: Props) {
  useEffect(() => {
    onListo();
  }, [onListo]);

  return (
    <div className="ri-imprimible" style={ESTILO_RAIZ}>
      <style>{CSS_IMPRESION}</style>
      <EncabezadoImprimible reporte={reporte} generadoEn={generadoEn} />
      <KpisImprimibles reporte={reporte} />
      <OportunidadesImprimible reporte={reporte} />
      {/* Alturas fijas, como el legacy: el PDF no depende del alto de la ventana. */}
      <div style={SECCION}>
        <GraficoEvolucion reporte={reporte} alto={200} claro />
      </div>
      <div style={SECCION}>
        <GraficoCategorias reporte={reporte} alto={240} claro />
      </div>
      <div style={SECCION}>
        <GraficoSubcategorias reporte={reporte} alto={280} claro />
      </div>
      <div style={SECCION}>
        <GraficoSucursales reporte={reporte} alto={240} claro />
      </div>
      <DetalleImprimible reporte={reporte} incidentes={incidentes} />
      <footer
        className="ri-pie"
        style={{ marginTop: 24, paddingTop: 8, borderTop: `1px solid ${BORDE}`, fontSize: 10, color: GRIS }}
      >
        Canal Directo · Confidencial — Uso exclusivo del Directorio
      </footer>
    </div>
  );
}
