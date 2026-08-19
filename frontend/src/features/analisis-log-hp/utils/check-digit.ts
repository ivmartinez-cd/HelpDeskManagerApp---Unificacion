/** Dígito verificador de Canal Directo (algoritmo 3-1 mod 10, igual al legacy). */
export function calcCheckDigit(numStr: string): string {
  const clean = numStr.replace(/\D/g, "");
  if (!clean) return "";
  let sum = 0;
  for (let i = 0; i < clean.length; i++) {
    sum += Number(clean[i]) * (i % 2 === 0 ? 3 : 1);
  }
  return String((10 - (sum % 10)) % 10);
}

export function formatIncidentNumber(numero: string): string {
  const cd = calcCheckDigit(numero);
  return cd ? `${numero}-${cd}` : numero;
}
