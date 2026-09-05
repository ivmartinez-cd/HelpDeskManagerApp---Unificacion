export function formatARS(n: number) {
  return n.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 2 });
}

export function formatFecha(iso: string) {
  const d = new Date(iso);
  return `${d.getDate()}/${d.getMonth() + 1}/${d.getFullYear()}`;
}

// Para fechas date-only ("YYYY-MM-DD"): new Date() las parsea como UTC y en
// timezone AR (UTC-3) formatFecha mostraría el día anterior.
export function formatFechaDia(isoDate: string) {
  const [y, m, d] = isoDate.split("-");
  return `${d}/${m}/${y}`;
}

/** Resumen del import CSV (upsert): antes el toast solo decía "creados" — con
 * reimportar el mismo archivo casi siempre en 0, y sin ningún rastro de
 * cuántas filas se descartaron por datos inválidos. */
export function resumenImportCsv(
  res: { creados: number; actualizados: number; sinCambios: number; descartadas: number },
  singular: string,
  plural: string,
): string {
  const nombre = (n: number) => (n === 1 ? singular : plural);
  const partes: string[] = [];
  if (res.creados) partes.push(`${res.creados} ${nombre(res.creados)} nueva${res.creados === 1 ? "" : "s"}`);
  if (res.actualizados) partes.push(`${res.actualizados} actualizada${res.actualizados === 1 ? "" : "s"}`);
  if (res.sinCambios) partes.push(`${res.sinCambios} sin cambios`);
  if (partes.length === 0) partes.push(`0 ${plural} procesadas`);
  const base = partes.join(", ");
  return res.descartadas > 0 ? `${base} — ${res.descartadas} descartada${res.descartadas === 1 ? "" : "s"} (ver logs)` : base;
}
