import type {
  Cobertura,
  CoberturaEstadoUi,
  FilaCoberturas,
  Intercambio,
  IntercambioPayload,
} from "../types/coberturas";
import { deriveEstado } from "./estado";

/** El listado del backend es plano (una fila por cobertura, ADR-026 no
 * rompe ese contrato): acá se agrupan las dos mitades de cada intercambio
 * en una sola fila. Un `intercambioId` que no tenga exactamente dos
 * mitades (no debería pasar: el backend las crea y cancela juntas) se
 * muestra como coberturas sueltas antes que ocultarlo. */
export function agruparFilas(coberturas: Cobertura[]): FilaCoberturas[] {
  const porIntercambio = new Map<string, Cobertura[]>();
  for (const c of coberturas) {
    if (c.intercambioId) {
      porIntercambio.set(c.intercambioId, [...(porIntercambio.get(c.intercambioId) ?? []), c]);
    }
  }
  const filas: FilaCoberturas[] = [];
  const emitidos = new Set<string>();
  for (const c of coberturas) {
    const mitades = c.intercambioId ? porIntercambio.get(c.intercambioId) : undefined;
    if (!c.intercambioId || !mitades || mitades.length !== 2) {
      filas.push({ tipo: "cobertura", cobertura: c });
      continue;
    }
    if (emitidos.has(c.intercambioId)) continue;
    emitidos.add(c.intercambioId);
    const [ida, vuelta] = mitades;
    filas.push({ tipo: "intercambio", intercambio: { id: c.intercambioId, ida, vuelta } });
  }
  return filas;
}

export function filaKey(fila: FilaCoberturas): string {
  return fila.tipo === "cobertura" ? fila.cobertura.id : `intercambio:${fila.intercambio.id}`;
}

/** Las dos mitades comparten fechas y estado por construcción: alcanza con
 * mirar la ida. */
export function estadoFila(fila: FilaCoberturas): CoberturaEstadoUi {
  return deriveEstado(fila.tipo === "cobertura" ? fila.cobertura : fila.intercambio.ida);
}

export function filaCoincide(fila: FilaCoberturas, q: string): boolean {
  const campos =
    fila.tipo === "cobertura"
      ? [fila.cobertura.ausenteNombre, fila.cobertura.reemplazanteNombre,
         fila.cobertura.ausenteId, fila.cobertura.reemplazanteId]
      : [fila.intercambio.ida.ausenteNombre, fila.intercambio.vuelta.ausenteNombre,
         fila.intercambio.ida.ausenteId, fila.intercambio.vuelta.ausenteId];
  return campos
    .filter((v): v is string => v !== null)
    .some((v) => v.toLowerCase().includes(q));
}

export function nombreOperadorA(i: Intercambio): string {
  return i.ida.ausenteNombre ?? i.ida.ausenteId;
}

export function nombreOperadorB(i: Intercambio): string {
  return i.vuelta.ausenteNombre ?? i.vuelta.ausenteId;
}

/** Payload de edición a partir del par: A = ausente de la ida, B = ausente
 * de la vuelta; cada alcance es el de su propia mitad. */
export function intercambioAPayload(i: Intercambio): IntercambioPayload {
  return {
    operadorAId: i.ida.ausenteId,
    operadorBId: i.vuelta.ausenteId,
    desde: i.ida.desde,
    hasta: i.ida.hasta,
    alcanceItemsA: i.ida.alcanceTotal ? null : i.ida.alcanceItems,
    alcanceItemsB: i.vuelta.alcanceTotal ? null : i.vuelta.alcanceItems,
    motivo: i.ida.motivo,
  };
}
