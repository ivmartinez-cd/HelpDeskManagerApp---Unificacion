"use client";

import { useRef, useState } from "react";
import { toast } from "sonner";

/** Port de `Printer-Logs-Analyzer/frontend/src/hooks/useExportPdf.ts`: abre un
 * popup con el reporte ejecutivo clonado + los estilos actuales, espera fuentes
 * e imágenes, y dispara `window.print()` (PDF vía "Guardar como PDF" del
 * navegador — sin jsPDF/html2canvas, igual que el legacy). */

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function buildHeadMarkup(title: string): string {
  const styleNodes = Array.from(document.querySelectorAll('link[rel="stylesheet"], style'));
  const stylesMarkup = styleNodes
    .map((node) =>
      node.tagName === "LINK"
        ? `<link rel="stylesheet" href="${escapeHtml((node as HTMLLinkElement).href)}">`
        : node.outerHTML,
    )
    .join("\n");

  return `
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${escapeHtml(title)}</title>
    <base href="${escapeHtml(document.baseURI)}">
    ${stylesMarkup}
    <style>
      @page { size: A4 portrait; margin: 0; }
      html, body { margin: 0; padding: 0; background: #0e0e10; }
      body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      .print-shell { min-height: 100vh; display: flex; justify-content: center; padding: 16px 0; box-sizing: border-box; }
      @media print {
        html, body { background: #ffffff; }
        .print-shell { padding: 0; }
      }
    </style>
  `;
}

async function waitForImages(doc: Document): Promise<void> {
  const images = Array.from(doc.images).filter((img) => !img.complete);
  await Promise.all(
    images.map(
      (img) =>
        new Promise<void>((resolve) => {
          img.addEventListener("load", () => resolve(), { once: true });
          img.addEventListener("error", () => resolve(), { once: true });
        }),
    ),
  );
}

async function waitForPrintReady(printWindow: Window): Promise<void> {
  const fonts = printWindow.document.fonts;
  if (fonts?.ready) {
    try {
      await fonts.ready;
    } catch {
      /* seguir con fallbacks del sistema */
    }
  }
  await waitForImages(printWindow.document);
  await new Promise<void>((resolve) => {
    printWindow.requestAnimationFrame(() => {
      printWindow.requestAnimationFrame(() => resolve());
    });
  });
}

export function useExportPdf(fileStem: string) {
  const [exportingPdf, setExportingPdf] = useState(false);
  const printReportRef = useRef<HTMLDivElement>(null);

  async function handleExportPdf(onBeforePrint?: () => Promise<void>) {
    setExportingPdf(true);
    try {
      if (onBeforePrint) await onBeforePrint();

      const reportMarkup = printReportRef.current?.outerHTML;
      if (!reportMarkup) {
        toast.error("No se pudo preparar el reporte ejecutivo");
        return;
      }

      const printWindow = window.open("", "_blank");
      if (!printWindow) {
        toast.error("El navegador bloqueó la ventana emergente. Permití popups para este sitio.");
        return;
      }

      const title = `Reporte_Ejecutivo_${fileStem}`;
      printWindow.document.open();
      printWindow.document.write(
        `<!doctype html><html lang="es"><head>${buildHeadMarkup(title)}</head>` +
          `<body><main class="print-shell">${reportMarkup}</main></body></html>`,
      );
      printWindow.document.close();
      printWindow.document.title = title;

      await waitForPrintReady(printWindow);
      printWindow.focus();
      printWindow.print();
      printWindow.onafterprint = () => {
        setTimeout(() => {
          if (!printWindow.closed) printWindow.close();
        }, 150);
      };
    } catch (err) {
      console.error("Error al preparar el reporte ejecutivo:", err);
      toast.error("Error al preparar el PDF para impresión");
    } finally {
      setExportingPdf(false);
    }
  }

  return { exportingPdf, handleExportPdf, printReportRef };
}
