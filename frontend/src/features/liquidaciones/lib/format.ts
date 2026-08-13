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
