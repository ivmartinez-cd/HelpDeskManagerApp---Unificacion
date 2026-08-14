const WEB_AGENTES_INCIDENTS = "https://webagentes.canaldirecto.com.ar/incidents/view";

function checkDigit(nro: number | string): number {
  return String(nro)
    .split("")
    .filter((c) => c >= "0" && c <= "9")
    .reduce((acc, d) => acc + Number(d), 0) % 10;
}

export function incidentUrl(nro: number | string): string {
  return `${WEB_AGENTES_INCIDENTS}/${nro}-${checkDigit(nro)}`;
}
