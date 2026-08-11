import { formatArgDate, formatPlainDate } from "../../utils/format";

/** Modo impresión del detalle de cliente (`@media print`).
 *
 * El CSS va en un `<style>` montado por esta pantalla y no en `globals.css`: es
 * la única vista imprimible del módulo y así las reglas no existen mientras el
 * usuario está en cualquier otra pantalla.
 *
 * Qué hace, en orden:
 *  - Esconde el shell (`header`/`aside` del layout de la app) y todo lo marcado
 *    con `data-print-hide` (selector de fechas, botón Imprimir, volver).
 *  - Suelta las alturas: el layout de la app es `h-screen` con un `main`
 *    scrolleable, que al imprimir recortaría el reporte a una sola página.
 *  - Muestra el header/pie de impresión (`data-print-only`, ocultos en pantalla).
 *  - Fuerza blanco y negro: el tema oscuro imprimiría cajas negras, y el
 *    handoff pide los gráficos en escala de grises (`filter: grayscale(1)`).
 */
const PRINT_CSS = `
@media print {
  @page { margin: 14mm; }
  html, body {
    height: auto !important;
    background: #fff !important;
  }
  main,
  main > div,
  main > div > div {
    display: block !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
    overflow: visible !important;
  }
  /* La barra superior del layout, no cualquier <header>: los cards de la
     pantalla también usan <header> para su título y esos sí se imprimen. */
  main > div > header,
  aside,
  [data-print-hide] { display: none !important; }
  /* Los únicos botones del área imprimible son las pills de período del
     gráfico: en papel no son interactivas, solo ruido. */
  [data-print-root] button { display: none !important; }
  [data-print-only] { display: block !important; }
  [data-print-root] {
    padding: 0 !important;
    background: #fff !important;
  }
  [data-print-root] *:not(canvas) {
    color: #111 !important;
    background-color: transparent !important;
    border-color: #d4d4d4 !important;
    box-shadow: none !important;
  }
  [data-print-card] {
    break-inside: avoid;
    page-break-inside: avoid;
  }
  canvas { filter: grayscale(1) !important; }
}
`;

export function ClientePrintStyles() {
  return <style>{PRINT_CSS}</style>;
}

interface ClientePrintHeaderProps {
  customerName: string;
  startDate: string;
  endDate: string;
}

/** Encabezado alternativo que solo existe en el papel (el de pantalla tiene
 * botones y selector de rango, que no se imprimen). */
export function ClientePrintHeader({ customerName, startDate, endDate }: ClientePrintHeaderProps) {
  return (
    <div
      data-print-only
      className="mb-6 hidden border-b border-[#d4d4d4] pb-4"
      aria-hidden="true"
    >
      {/* eslint-disable-next-line @next/next/no-img-element -- SVG de marca, next/image no aporta */}
      <img src="/logo.svg" alt="Canal Directo" className="h-[34px] w-auto object-contain" />
      <div className="mt-3 font-heading text-lg font-extrabold">
        Reporte de insumos · {customerName}
      </div>
      <div className="font-body text-sm">
        Período: {formatPlainDate(startDate)} – {formatPlainDate(endDate)}
      </div>
    </div>
  );
}

export function ClientePrintFooter() {
  return (
    <div
      data-print-only
      className="mt-6 hidden border-t border-[#d4d4d4] pt-3 font-body text-xs"
      aria-hidden="true"
    >
      Generado por Mesa de Ayuda · Canal Directo · {formatArgDate(new Date().toISOString())}
    </div>
  );
}
