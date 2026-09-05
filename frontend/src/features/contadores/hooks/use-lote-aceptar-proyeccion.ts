import { useCallback, useMemo, useState } from "react";
import { toast } from "sonner";
import { proyeccionApi } from "../api/proyeccion-api";
import type { FilaProyeccion, TableroProyeccion } from "../types/proyeccion";
import { claveFila, esSeleccionable } from "../components/proyeccion-tabla";

/** Acciones masivas (REGLAS_DE_NEGOCIO §14): aplicar "aceptar" a varias filas
 * a la vez, reusando el mismo endpoint por-fila que ya usa el drawer. Las
 * filas sin `estim_propuesto` (reales, o bloqueadas por `bloqueo_obligatorio`
 * — ver `_resolver_resultado_final.py`) quedan afuera de la selección: no
 * hay nada calculado para confirmar de una, requieren revisión individual. */
export function useLoteAceptarProyeccion(
  tablero: TableroProyeccion | null,
  filasVisibles: FilaProyeccion[],
  onAceptado: () => void,
) {
  const [seleccionadasRaw, setSeleccionadasRaw] = useState<Set<string>>(new Set());
  const [aceptando, setAceptando] = useState(false);

  // Derivado en vez de resetear estado a mano cuando cambia `tablero`
  // (react-hooks/set-state-in-effect): una clave de un tablero anterior
  // (equipo/clase que ya no está en la grilla actual) queda filtrada acá
  // sin necesidad de un efecto que la limpie.
  const clavesVigentes = useMemo(
    () => new Set((tablero?.filas ?? []).map(claveFila)),
    [tablero],
  );
  const seleccionadas = useMemo(
    () => new Set([...seleccionadasRaw].filter((c) => clavesVigentes.has(c))),
    [seleccionadasRaw, clavesVigentes],
  );

  const toggleSeleccion = useCallback((fila: FilaProyeccion) => {
    setSeleccionadasRaw((prev) => {
      const next = new Set(prev);
      const clave = claveFila(fila);
      if (next.has(clave)) next.delete(clave);
      else next.add(clave);
      return next;
    });
  }, []);

  const toggleSeleccionTodas = useCallback(() => {
    setSeleccionadasRaw((prev) => {
      const seleccionables = filasVisibles.filter(esSeleccionable);
      const todasYa = seleccionables.length > 0 && seleccionables.every((f) => prev.has(claveFila(f)));
      const next = new Set(prev);
      for (const f of seleccionables) {
        if (todasYa) next.delete(claveFila(f));
        else next.add(claveFila(f));
      }
      return next;
    });
  }, [filasVisibles]);

  const limpiarSeleccion = useCallback(() => setSeleccionadasRaw(new Set()), []);

  const aceptarSeleccionadas = useCallback(async () => {
    if (!tablero) return;
    const filas = tablero.filas.filter((f) => seleccionadas.has(claveFila(f)));
    if (filas.length === 0) return;
    setAceptando(true);
    const resultados = await Promise.allSettled(
      filas.map((f) =>
        proyeccionApi.aceptarPropuesta(f.id_maquina, f.clase, {
          contador_propuesto: f.estim_propuesto,
          tipo_toma: f.tipo_toma,
          fuente: f.fuente,
          metodo_detalle: f.metodo_detalle,
        }),
      ),
    );
    setAceptando(false);
    const fallidas = resultados.filter((r) => r.status === "rejected").length;
    const aceptadas = resultados.length - fallidas;
    if (aceptadas > 0) toast.success(`${aceptadas} propuesta(s) aceptada(s)`);
    if (fallidas > 0) toast.error(`${fallidas} fallaron — revisalas de a una desde el panel de candidatos`);
    onAceptado();
  }, [tablero, seleccionadas, onAceptado]);

  return { seleccionadas, aceptando, toggleSeleccion, toggleSeleccionTodas, limpiarSeleccion, aceptarSeleccionadas };
}
