/** Helpers puros para el input de hora HH:MM de TimeInput: un solo campo
 * enmascarado, sin segmentos separados. Todo el estado vive como una
 * cadena de hasta 4 dígitos ("HHMM") derivada del contenido completo del
 * campo en cada tecla — nunca de "cuál fue el último dígito tipeado", que
 * con un input controlado depende de dónde quedó el cursor y podía perder
 * o trasponer caracteres (p.ej. tipear "12" terminaba en "01"). */

export function digitosDeValor(value: string): string {
  return value.replace(/\D/g, "").slice(0, 4);
}

export function digitosDeRaw(raw: string): string {
  return raw.replace(/\D/g, "").slice(0, 4);
}

/** Texto a mostrar mientras se tipea: clampea cada parte apenas tiene 2
 * dígitos (hora ≤23, minutos ≤59) e inserta ":" al pasar a los minutos. */
export function formatearDigitos(digitos: string): string {
  const hh = digitos.slice(0, 2);
  const mm = digitos.slice(2, 4);
  const hhVisible = hh.length === 2 ? String(Math.min(Number(hh), 23)).padStart(2, "0") : hh;
  const mmVisible = mm.length === 2 ? String(Math.min(Number(mm), 59)).padStart(2, "0") : mm;
  return digitos.length <= 2 ? hhVisible : `${hhVisible}:${mmVisible}`;
}

/** Al perder el foco con una parte a medio tipear (1 o 3 dígitos), la
 * completa con cero a la izquierda en vez de dejarla inválida. */
export function completarAlDesenfocar(digitos: string): string {
  const hh = digitos.slice(0, 2);
  const mm = digitos.slice(2, 4);
  const hhPad = hh.length === 1 ? hh.padStart(2, "0") : hh;
  const mmPad = mm.length === 1 ? mm.padStart(2, "0") : mm;
  return hhPad + mmPad;
}

/** "HH:MM" final clampeado, o "" si todavía falta algún dígito. */
export function aHhmm(digitos: string): string {
  if (digitos.length < 4) return "";
  const hh = Math.min(Number(digitos.slice(0, 2)), 23);
  const mm = Math.min(Number(digitos.slice(2, 4)), 59);
  return `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}`;
}
