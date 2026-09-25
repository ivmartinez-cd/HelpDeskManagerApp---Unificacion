"use client";

import dynamic from "next/dynamic";
import { FileDown, Loader2 } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import type { EstadoDashboard } from "../../hooks/use-reporte";
import { useExportarPdfReporte } from "../../hooks/use-exportar-pdf-reporte";
import { CLASE_BOTON } from "../tabla/estilos";

// chart.js y el imprimible fuera del bundle inicial: solo se cargan al exportar.
const ReporteImprimible = dynamic(() => import("./reporte-imprimible").then((m) => m.ReporteImprimible), {
  ssr: false,
});

/** "Exportar PDF": reporte ejecutivo del cliente y rango actuales, siempre sin
 * los filtros interactivos (decisión del legacy). */
export function BotonExportarPdf({ estado }: { estado: EstadoDashboard }) {
  const { exportar, ocupado, datos, alListo, printReportRef } = useExportarPdfReporte(estado);
  return (
    <>
      <Button
        variant="outline"
        className={CLASE_BOTON}
        onClick={exportar}
        disabled={ocupado || !estado.pedido || !estado.reporte}
        title="Exportar el reporte ejecutivo a PDF (período completo, sin filtros)"
      >
        {ocupado ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : (
          <FileDown className="h-4 w-4" aria-hidden="true" />
        )}
        {ocupado ? "Preparando…" : "Exportar PDF"}
      </Button>
      {datos && (
        // Fuera de pantalla pero con layout real (no display:none): Chart.js
        // necesita medir el contenedor para dibujar.
        <div aria-hidden="true" style={{ position: "fixed", top: 0, left: -99999, pointerEvents: "none" }}>
          <div ref={printReportRef}>
            <ReporteImprimible {...datos} onListo={alListo} />
          </div>
        </div>
      )}
    </>
  );
}
