const RADIO_ENCUADRE_KM = 150;

function mediana(valores: number[]): number {
  const ordenados = [...valores].sort((a, b) => a - b);
  const medio = Math.floor(ordenados.length / 2);
  return ordenados.length % 2 !== 0
    ? ordenados[medio]
    : (ordenados[medio - 1] + ordenados[medio]) / 2;
}

function haversineKm(a: [number, number], b: [number, number]): number {
  const R = 6371;
  const dLat = ((b[0] - a[0]) * Math.PI) / 180;
  const dLon = ((b[1] - a[1]) * Math.PI) / 180;
  const lat1 = (a[0] * Math.PI) / 180;
  const lat2 = (b[0] * Math.PI) / 180;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

/** Encuadra por la mediana del grupo, no por el bbox de todos los puntos:
 * una sola sucursal con coordenada mal cargada en Siges (dentro del bbox de
 * Argentina, pero a cientos de km de su zona real — visto en CABA apuntando
 * cerca de Bahía Blanca) no debe forzar un zoom alejado que oculte el resto.
 * El punto igual se sigue dibujando como marcador, solo no cuenta para el
 * encuadre inicial. */
export function puntosParaEncuadre(puntos: [number, number][]): [number, number][] {
  if (puntos.length <= 2) return puntos;
  const centro: [number, number] = [
    mediana(puntos.map((p) => p[0])),
    mediana(puntos.map((p) => p[1])),
  ];
  const cercanos = puntos.filter((p) => haversineKm(p, centro) <= RADIO_ENCUADRE_KM);
  return cercanos.length >= 2 ? cercanos : puntos;
}
