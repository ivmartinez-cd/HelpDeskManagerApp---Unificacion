/** Formatos de la Proyección, iguales a los del Estimador v1.7: números con
 * `N0`/`N2` en cultura es-AR (punto de miles, redondeo "medio lejos del
 * cero", que es también el default de Intl) y fechas `dd/MM/yy` o
 * `dd/MM/yyyy`. Sin JSX: vive como .tsx solo por convención de nombres del
 * feature. */

const formatoN0 = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 0 });
const formatoN2 = new Intl.NumberFormat("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** `N0` es-AR; "—" si no hay valor. */
export function n0(v: number | null | undefined): string {
  return v === null || v === undefined ? "—" : formatoN0.format(v);
}

/** `N2` es-AR; "—" si no hay valor. */
export function n2(v: number | null | undefined): string {
  return v === null || v === undefined ? "—" : formatoN2.format(v);
}

function partes(iso: string): [string, string, string] {
  const [y, m, d] = iso.slice(0, 10).split("-");
  return [y, m, d];
}

/** `dd/MM/yy`; "—" si no hay fecha. */
export function fechaCorta(iso: string | null | undefined): string {
  if (!iso) return "—";
  const [y, m, d] = partes(iso);
  return `${d}/${m}/${y.slice(2)}`;
}

/** `dd/MM/yyyy`; "—" si no hay fecha. */
export function fechaLarga(iso: string | null | undefined): string {
  if (!iso) return "—";
  const [y, m, d] = partes(iso);
  return `${d}/${m}/${y}`;
}

/** `T{n}`; "—" si no hay tipo. */
export function tipoToma(t: number | null | undefined): string {
  return t === null || t === undefined ? "—" : `T${t}`;
}

/** `TipoEstimStr` del legacy: tipo sugerido del estimado. */
export function tipoEstim(t: number | null): string {
  if (t === null) return "—";
  return t === 4 ? "⚠ T4" : `T${t}`;
}

/** `Math.Round(x, 0)` de C# sobre decimal: redondeo bancario (al par). */
export function redondeoBancario(x: number): number {
  const piso = Math.floor(x);
  const resto = x - piso;
  if (Math.abs(resto - 0.5) > 1e-9) return Math.round(x);
  return piso % 2 === 0 ? piso : piso + 1;
}

/** Días entre dos fechas ISO (`DayNumber` de .NET): b − a. */
export function diasEntre(a: string, b: string): number {
  const ms = Date.UTC(...ymd(b)) - Date.UTC(...ymd(a));
  return Math.round(ms / 86_400_000);
}

function ymd(iso: string): [number, number, number] {
  const [y, m, d] = partes(iso);
  return [Number(y), Number(m) - 1, Number(d)];
}

export const TEC_LABEL = { MONO: "Mono", COLOR: "Color" } as const;

/** Comparador de strings con la cultura es-AR (el `OrderBy` del legacy). */
export const compararEsAr = new Intl.Collator("es-AR").compare;
