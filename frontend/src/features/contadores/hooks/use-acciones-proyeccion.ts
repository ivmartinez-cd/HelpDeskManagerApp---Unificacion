import { useState } from "react";
import { mensajeError, proyeccionApi, seleccionBody } from "../api/proyeccion-api";
import type { ContextoProceso, FilaProyeccion, MetodoForzado } from "../types/proyeccion";
import { elegida, type Seleccion } from "./use-candidatos-proyeccion";

/** Acciones del panel de candidatos (handlers de `GrillaEstimacion.razor`
 * v1.7). Cada una se guarda como decisión del proceso; al terminar bien el
 * panel se cierra y la grilla se relee (`onHecho`), como el legacy. Si la
 * API la rechaza (422/404) el mensaje queda visible en el panel.
 *
 * La observación escrita viaja solo con "Aceptar P/L manual" y "Marcar
 * pendiente": "Aceptar sugerencia" la descarta (`observacion: null`). */

const limpia = (nota: string) => (nota.trim() ? nota.trim() : null);

function useEjecutor(onHecho: () => void) {
  const [guardando, setGuardando] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ejecutar = async (accion: string, fn: () => Promise<unknown>) => {
    setGuardando(accion);
    setError(null);
    try {
      await fn();
      onHecho();
    } catch (err) {
      setError(mensajeError(err, "No se pudo guardar la acción."));
    } finally {
      setGuardando(null);
    }
  };
  return { guardando, error, ejecutar };
}

export function useAccionesProyeccion(fila: FilaProyeccion, contexto: ContextoProceso, onHecho: () => void) {
  const { guardando, error, ejecutar } = useEjecutor(onHecho);
  const base = seleccionBody(contexto);
  const { id_maquina: id, clase } = fila;
  const aceptar = (body: Parameters<typeof proyeccionApi.aceptar>[2]) => proyeccionApi.aceptar(id, clase, body);
  return {
    guardando,
    error,
    aceptarPL: (s: Seleccion, nota: string) =>
      ejecutar("aceptar", () =>
        aceptar({ ...base, nota: limpia(nota), partida: elegida(s.partida!), llegada: elegida(s.llegada!) }),
      ),
    aceptarSugerencia: () => ejecutar("aceptar", () => aceptar(base)),
    marcarPendiente: (nota: string) =>
      ejecutar("pendiente", () => proyeccionApi.marcarPendiente(id, clase, { ...base, nota: limpia(nota) })),
    forzar: (metodo: MetodoForzado) =>
      ejecutar(metodo, () => proyeccionApi.forzarMetodo({ id_maquina: id, clase, metodo, ...base })),
  };
}
