export const numberFormat = new Intl.NumberFormat("es-AR");

export function formatConsultadoEn(iso: string): string {
  return new Date(iso).toLocaleString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
