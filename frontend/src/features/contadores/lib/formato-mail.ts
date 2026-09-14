import type { DetalleContadorRow } from "../types/detalle-contador-proceso";
import { ISOTIPO_WHITE_BASE64 } from "./isotipo-mail-base64";

// Formato para pegar en un mail — subconjunto de columnas del XLSX
// (`openpyxl_detalle_contador_writer.py`): sin las fechas/contadores/tipo/
// clase (ruido para el cliente final, pedido de Mariana 14/9) ni el N° de
// proceso en el título (interno, no le importa al cliente). `vertical-align:
// top` + `white-space:nowrap` (layout automático, sin anchos fijos): sin
// esto, en pantallas anchas Gmail/Outlook parte el texto en dos líneas
// dentro de la celda y desalinea filas (reportado por Mariana, capturas
// 14/9). Estilos inline (no `<style>`/clases): los clientes de mail
// descartan CSS externo al pegar HTML desde el portapapeles.

const _NARANJA = "#F7941D";
const _GRIS = "#58595B";
const _BORDE = "#DDDDDD";
const _FUENTE = "Tahoma, Arial, sans-serif";

const COLUMNAS: { label: string }[] = [
  { label: "Empresa" },
  { label: "Sucursal" },
  { label: "Modelo" },
  { label: "Serie" },
  { label: "Sector" },
  { label: "Estado Máquina" },
  { label: "Dirección IP" },
  { label: "Máscara IP" },
];

function escapeHtml(valor: string): string {
  return valor
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function ordenarPorSucursal(filas: DetalleContadorRow[]): DetalleContadorRow[] {
  return [...filas].sort(
    (a, b) =>
      a.empresa.localeCompare(b.empresa, "es") || a.sucursal.localeCompare(b.sucursal, "es"),
  );
}

function celdasFila(fila: DetalleContadorRow): string[] {
  return [
    fila.empresa,
    fila.sucursal,
    fila.modelo,
    fila.serie,
    fila.sector ?? "",
    fila.estado_maquina ?? "",
    fila.direccion_ip ?? "",
    fila.mascara_ip ?? "",
  ];
}

const TD_ESTILO = `border-bottom:1px solid ${_BORDE};padding:4px 8px;font-family:${_FUENTE};font-size:10pt;vertical-align:top;white-space:nowrap;`;

function filaHtml(fila: DetalleContadorRow): string {
  const celdas = celdasFila(fila)
    .map((valor) => `<td style="${TD_ESTILO}">${escapeHtml(valor)}</td>`)
    .join("");
  return `<tr>${celdas}</tr>`;
}

export function formatearTablaMailHtml(filasSinOrdenar: DetalleContadorRow[], cliente: string): string {
  const filas = ordenarPorSucursal(filasSinOrdenar);
  const total = filas.length;
  const encabezado = COLUMNAS.map(
    (c) =>
      `<th style="background-color:${_GRIS};color:#FFFFFF;font-weight:bold;font-family:${_FUENTE};font-size:10pt;padding:6px 8px;text-align:left;vertical-align:top;white-space:nowrap;">${escapeHtml(c.label)}</th>`,
  ).join("");

  return (
    // `table-layout:auto` (default) + `white-space:nowrap` en las celdas:
    // que la columna crezca según su contenido más largo, en vez de partir
    // el texto en dos líneas (queja de la TL, ver captura 14/9).
    `<table cellspacing="0" cellpadding="0" style="border-collapse:collapse;font-family:${_FUENTE};">` +
    `<tr><td colspan="${COLUMNAS.length}" style="background-color:${_NARANJA};color:#FFFFFF;font-weight:bold;font-size:14pt;padding:8px 12px;font-family:${_FUENTE};">` +
    `<img src="data:image/png;base64,${ISOTIPO_WHITE_BASE64}" width="18" height="18" alt="" ` +
    `style="vertical-align:middle;margin-right:8px;" />` +
    `Detalle de Contadores — ${escapeHtml(cliente)}</td></tr>` +
    `<tr><td colspan="${COLUMNAS.length}" style="color:${_GRIS};font-style:italic;font-size:10pt;padding:4px 12px;font-family:${_FUENTE};">` +
    `${total} equipo${total !== 1 ? "s" : ""}</td></tr>` +
    `<tr>${encabezado}</tr>` +
    filas.map(filaHtml).join("") +
    `</table>`
  );
}

export function formatearTablaMailTexto(filasSinOrdenar: DetalleContadorRow[], cliente: string): string {
  const filas = ordenarPorSucursal(filasSinOrdenar);
  const encabezado = COLUMNAS.map((c) => c.label).join("\t");
  const cuerpo = filas.map((fila) => celdasFila(fila).join("\t")).join("\n");
  return `Detalle de Contadores — ${cliente}\n\n${encabezado}\n${cuerpo}`;
}
