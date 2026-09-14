import type { DetalleContadorRow } from "../types/detalle-contador-proceso";

// Formato para pegar en un mail — subconjunto de columnas del XLSX
// (`openpyxl_detalle_contador_writer.py`): sin las fechas/contadores/tipo/
// clase (ruido para el cliente final, pedido de Mariana 14/9) ni el N° de
// proceso en el título (interno, no le importa al cliente). Ancho fijo por
// columna + `vertical-align:top`: sin eso, en pantallas anchas el layout
// automático de la tabla en Gmail/Outlook desalinea filas cuando alguna
// celda envuelve a dos líneas (reportado por Mariana, captura 14/9).
// Estilos inline (no `<style>`/clases): los clientes de mail descartan CSS
// externo al pegar HTML desde el portapapeles.

const _NARANJA = "#F7941D";
const _GRIS = "#58595B";
const _BORDE = "#DDDDDD";
const _FUENTE = "Tahoma, Arial, sans-serif";

const COLUMNAS: { label: string; ancho: number }[] = [
  { label: "Empresa", ancho: 110 },
  { label: "Sucursal", ancho: 110 },
  { label: "Modelo", ancho: 150 },
  { label: "Serie", ancho: 90 },
  { label: "Sector", ancho: 90 },
  { label: "Estado Máquina", ancho: 100 },
  { label: "Dirección IP", ancho: 90 },
  { label: "Máscara IP", ancho: 90 },
];

function escapeHtml(valor: string): string {
  return valor
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
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

const TD_ESTILO = `border-bottom:1px solid ${_BORDE};padding:4px 8px;font-family:${_FUENTE};font-size:10pt;vertical-align:top;`;

function filaHtml(fila: DetalleContadorRow): string {
  const celdas = celdasFila(fila)
    .map((valor) => `<td style="${TD_ESTILO}">${escapeHtml(valor)}</td>`)
    .join("");
  return `<tr>${celdas}</tr>`;
}

export function formatearTablaMailHtml(filas: DetalleContadorRow[], cliente: string): string {
  const total = filas.length;
  const anchoTotal = COLUMNAS.reduce((suma, c) => suma + c.ancho, 0);
  const colgroup = COLUMNAS.map((c) => `<col style="width:${c.ancho}px;">`).join("");
  const encabezado = COLUMNAS.map(
    (c) =>
      `<th style="background-color:${_GRIS};color:#FFFFFF;font-weight:bold;font-family:${_FUENTE};font-size:10pt;padding:6px 8px;text-align:left;vertical-align:top;">${escapeHtml(c.label)}</th>`,
  ).join("");

  return (
    `<table cellspacing="0" cellpadding="0" style="border-collapse:collapse;table-layout:fixed;width:${anchoTotal}px;font-family:${_FUENTE};">` +
    `<colgroup>${colgroup}</colgroup>` +
    `<tr><td colspan="${COLUMNAS.length}" style="background-color:${_NARANJA};color:#FFFFFF;font-weight:bold;font-size:14pt;padding:8px 12px;font-family:${_FUENTE};">` +
    `Detalle de Contadores — ${escapeHtml(cliente)}</td></tr>` +
    `<tr><td colspan="${COLUMNAS.length}" style="color:${_GRIS};font-style:italic;font-size:10pt;padding:4px 12px;font-family:${_FUENTE};">` +
    `${total} equipo${total !== 1 ? "s" : ""}</td></tr>` +
    `<tr>${encabezado}</tr>` +
    filas.map(filaHtml).join("") +
    `</table>`
  );
}

export function formatearTablaMailTexto(filas: DetalleContadorRow[], cliente: string): string {
  const encabezado = COLUMNAS.map((c) => c.label).join("\t");
  const cuerpo = filas.map((fila) => celdasFila(fila).join("\t")).join("\n");
  return `Detalle de Contadores — ${cliente}\n\n${encabezado}\n${cuerpo}`;
}
