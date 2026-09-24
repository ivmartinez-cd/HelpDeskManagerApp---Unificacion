import { useCallback, useRef, useState } from "react";
import { mensajeError, proyeccionApi } from "../api/proyeccion-api";
import type {
  ContextoProceso,
  RestauracionDecisiones,
  SolicitudTableroReal,
  TableroProyeccion,
} from "../types/proyeccion";
import { useCombosProyeccion } from "./use-combos-proyeccion";

/** Carga del tablero y restauración de decisiones — `Index.razor` +
 * `GrillaEstimacion.RestaurarOverridesAsync` del Estimador v1.7:
 *
 * - Cambiar de grupo o de proceso limpia la grilla (hay que volver a Cargar).
 * - "Cargar" arma el tablero desde cero: restaura las decisiones del proceso
 *   y muestra el banner con lo restaurado en ESA carga. Un "Descartar y
 *   empezar limpio" anterior deja de valer (en el legacy vive en memoria y
 *   la próxima carga vuelve a restaurar todo).
 * - Después de una acción del operador el tablero se relee (`recargar`) sin
 *   tocar el banner y respetando el descarte vigente. */

interface Carga {
  tablero: TableroProyeccion | null;
  contexto: ContextoProceso;
  cargando: boolean;
  error: string | null;
  banner: RestauracionDecisiones | null;
  // Cuántas veces se apretó "Descartar y empezar limpio" (cierra el panel).
  descartes: number;
}

const SIN_CARGA: Carga = {
  tablero: null,
  contexto: { solicitud: undefined, descartarHasta: null },
  cargando: false,
  error: null,
  banner: null,
  descartes: 0,
};

// `r` puede faltar mientras el backend en ejecución sea anterior a este contrato.
function conAlgoRestaurado(r: RestauracionDecisiones | undefined): RestauracionDecisiones | null {
  return r && (r.restauradas > 0 || r.descartadas > 0) ? r : null;
}

/** Lee el tablero para `contexto`. Una carga nueva reemplaza el banner; una
 * relectura lo conserva. La respuesta de una lectura vieja se descarta. */
function useLectorTablero() {
  const [carga, setCarga] = useState<Carga>(SIN_CARGA);
  const secuencia = useRef(0);
  const leer = useCallback((contexto: ContextoProceso, esCargaNueva: boolean) => {
    const n = ++secuencia.current;
    const vigente = () => n === secuencia.current;
    setCarga((c) => (esCargaNueva ? { ...SIN_CARGA, cargando: true } : { ...c, cargando: true, error: null }));
    proyeccionApi
      .getTablero(contexto.solicitud, contexto.descartarHasta)
      .then((t) => vigente() && setCarga((c) => ({
        ...c, tablero: t, contexto, cargando: false, error: null,
        banner: esCargaNueva ? conAlgoRestaurado(t.restauracion) : c.banner,
      })))
      .catch((err) => vigente() && setCarga((c) => ({
        ...c, cargando: false, error: mensajeError(err, "Puede ser lenta o falló la conexión a Siges."),
      })));
  }, []);
  const limpiar = useCallback(() => {
    secuencia.current += 1;
    setCarga(SIN_CARGA);
  }, []);
  return { carga, setCarga, leer, limpiar };
}

export function useTableroProyeccion() {
  const { carga, setCarga, leer, limpiar } = useLectorTablero();
  const combos = useCombosProyeccion(limpiar);
  const { contexto, tablero } = carga;
  const cargar = useCallback(
    () => leer({ solicitud: combos.solicitudActual, descartarHasta: null }, true),
    [leer, combos.solicitudActual],
  );
  const recargar = useCallback(() => leer(contexto, false), [leer, contexto]);
  const descartarRestauracion = useCallback(() => {
    const descartarHasta = tablero?.restauracion?.vigentes_hasta ?? null;
    setCarga((c) => ({ ...c, banner: null, descartes: c.descartes + 1 }));
    leer({ solicitud: contexto.solicitud, descartarHasta }, false);
  }, [leer, setCarga, contexto, tablero]);
  const ocultarBanner = useCallback(() => setCarga((c) => ({ ...c, banner: null })), [setCarga]);
  const solicitudCargada: SolicitudTableroReal | undefined = contexto.solicitud;
  return { ...combos, ...carga, solicitudCargada, cargar, recargar, descartarRestauracion, ocultarBanner };
}
