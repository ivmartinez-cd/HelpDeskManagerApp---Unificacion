"use client";

import { useCallback, useRef, useState } from "react";
import { toast } from "sonner";
import { useExportPdf } from "@/shared/hooks/use-export-pdf";
import { reporteIncidentesApi } from "../api/reporte-incidentes-api";
import type { DatosImprimible } from "../components/imprimible/reporte-imprimible";
import { FILTROS_VACIOS } from "../lib/url-reporte";
import type { EstadoDashboard } from "./use-reporte";

const TOPE_DETALLE = 50;

function nombreArchivo(estado: EstadoDashboard): string {
  const cliente = (estado.reporte?.empresa.nombre ?? "cliente").replace(/[^\p{L}\p{N}]+/gu, "_");
  return `Incidentes_${cliente}_${estado.pedido?.periodo ?? ""}`;
}

function ventanaDeEspera(): Window | null {
  const ventana = window.open("", "_blank");
  ventana?.document.write("<p style='font-family:Arial;padding:24px'>Preparando el reporte…</p>");
  return ventana;
}

/** Exportar PDF: trae el reporte del período SIN filtros y los primeros 50
 * incidentes, monta el imprimible oculto y, cuando sus gráficos están
 * dibujados, lo pasa al hook compartido de impresión. El popup se abre en el
 * mismo click (antes del fetch) para que el navegador no lo bloquee. */
export function useExportarPdfReporte(estado: EstadoDashboard) {
  const { exportingPdf, handleExportPdf, printReportRef } = useExportPdf(nombreArchivo(estado));
  const [datos, setDatos] = useState<DatosImprimible | null>(null);
  const [preparando, setPreparando] = useState(false);
  const avisarListo = useRef<(() => void) | null>(null);

  const alListo = useCallback(() => avisarListo.current?.(), []);

  async function exportar() {
    const { pedido } = estado;
    if (!pedido) return;
    setPreparando(true);
    const ventana = ventanaDeEspera();
    try {
      const [reporte, incidentes] = await Promise.all([
        reporteIncidentesApi.getReporte(pedido, FILTROS_VACIOS),
        reporteIncidentesApi.listIncidentes(pedido, FILTROS_VACIOS, { page: 1, size: TOPE_DETALLE }),
      ]);
      const listo = new Promise<void>((resolver) => (avisarListo.current = resolver));
      setDatos({ reporte, incidentes, generadoEn: new Date().toISOString() });
      await listo;
      // Margen por si algún gráfico se redimensiona al montar. setTimeout y no
      // requestAnimationFrame: con el popup al frente esta pestaña queda oculta
      // y el navegador no le da frames.
      await new Promise<void>((r) => setTimeout(r, 100));
      await handleExportPdf(undefined, ventana);
    } catch (err: unknown) {
      console.error("Error al preparar el PDF del reporte de incidentes:", err);
      ventana?.close();
      toast.error(err instanceof Error ? err.message : "No se pudo preparar el PDF del reporte.");
    } finally {
      avisarListo.current = null;
      setDatos(null);
      setPreparando(false);
    }
  }

  return { exportar, ocupado: preparando || exportingPdf, datos, alListo, printReportRef };
}
