const WEB_AGENTES_INCIDENTS = "https://webagentes.canaldirecto.com.ar/incidents/view";

// Pesos alternados 3-1-3-1… de izquierda a derecha, igual que numeracion_ayc.py.
function checkDigit(base: number | string): number {
  const digits = String(base).replace(/-\d+$/, ""); // strip trailing -DV if present
  const sum = digits
    .split("")
    .reduce((acc, d, i) => acc + Number(d) * (i % 2 === 0 ? 3 : 1), 0);
  return (10 - (sum % 10)) % 10;
}

export function incidentUrl(nro: number | string): string {
  const base = String(nro).replace(/-\d+$/, ""); // normalise: strip any existing -DV
  return `${WEB_AGENTES_INCIDENTS}/${base}-${checkDigit(base)}`;
}
