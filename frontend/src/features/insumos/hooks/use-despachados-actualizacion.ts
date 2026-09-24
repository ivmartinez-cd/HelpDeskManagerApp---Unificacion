"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { ApiError } from "@/services/http-client";
import { despachadosApi } from "../api/despachados-api";
import type { CorridaDespachos, EstadoActualizacionDespachos } from "../types/despachados";
import { mensajeDeError } from "./use-despachados-listado";

/** "Última consulta a OCA" + "Actualizar ahora".
 *
 * El POST responde 202 enseguida (la corrida sigue en segundo plano en el
 * backend): mientras `/actualizacion` diga `enCurso`, se pollea cada
 * `POLL_MS`; cuando pasa a terminada se llama `onTermino` (la vista refresca
 * todo) y se muestra el toast con el resultado. Un 409 significa que ya hay
 * una corrida (el job programado u otro operador): se avisa y se sigue esa. */

const POLL_MS = 3_000;
/** Tope de seguimiento (10 min): una corrida que quedó colgada en la base por
 * un reinicio figura `enCurso` para siempre; el backend igual deja lanzar otra,
 * así que el botón no puede quedar bloqueado. */
const MAX_POLLS = 200;
/** Si tras varios polls la base no muestra ni la corrida en curso ni una
 * terminada nueva (la tarea tardó en registrarse), se da por terminada. */
const POLLS_GRACIA = 5;

export interface DespachadosActualizacionState {
  estado: EstadoActualizacionDespachos | null;
  enCurso: boolean;
  lanzando: boolean;
  actualizar: () => Promise<void>;
}

function avisarResultado(corrida: CorridaDespachos | null) {
  if (!corrida) return;
  if (corrida.error) {
    toast.error(`La actualización terminó con error: ${corrida.error}`);
    return;
  }
  const errores = corrida.consultasError
    ? ` · ${corrida.consultasError} guía(s) sin respuesta de OCA`
    : "";
  toast.success(`Estados actualizados desde OCA (${corrida.consultasOk} consultadas${errores})`);
}

export function useDespachadosActualizacion(onTermino: () => void): DespachadosActualizacionState {
  const [estado, setEstado] = useState<EstadoActualizacionDespachos | null>(null);
  const [lanzando, setLanzando] = useState(false);
  const [siguiendo, setSiguiendo] = useState(false);
  const estadoRef = useRef<EstadoActualizacionDespachos | null>(null);
  const idPrevio = useRef<number | null>(null);
  const onTerminoRef = useRef(onTermino);
  useEffect(() => {
    onTerminoRef.current = onTermino;
  }, [onTermino]);

  const consultar = useCallback(async () => {
    try {
      const nuevo = await despachadosApi.getActualizacion();
      estadoRef.current = nuevo;
      setEstado(nuevo);
      return nuevo;
    } catch (err) {
      // El estado de la corrida es informativo: si falla se deja el último.
      console.warn("[despachados] no se pudo leer el estado de la actualización:", err);
      return null;
    }
  }, []);

  const seguir = useCallback(() => {
    idPrevio.current = estadoRef.current?.ultimaTerminada?.id ?? null;
    setSiguiendo(true);
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- carga inicial, mismo patrón que use-historial-pending-orders
    void consultar().then((inicial) => {
      if (inicial?.enCurso) seguir();
    });
  }, [consultar, seguir]);

  useEffect(() => {
    if (!siguiendo) return;
    let intentos = 0;
    const timer = window.setInterval(async () => {
      intentos += 1;
      const nuevo = await consultar();
      if (intentos >= MAX_POLLS) {
        window.clearInterval(timer);
        setSiguiendo(false);
        return;
      }
      if (!nuevo || nuevo.enCurso) return;
      const terminadaNueva = (nuevo.ultimaTerminada?.id ?? null) !== idPrevio.current;
      if (!terminadaNueva && intentos < POLLS_GRACIA) return;
      window.clearInterval(timer);
      setSiguiendo(false);
      if (terminadaNueva) avisarResultado(nuevo.ultimaTerminada);
      onTerminoRef.current();
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [siguiendo, consultar]);

  const actualizar = useCallback(async () => {
    setLanzando(true);
    try {
      await despachadosApi.actualizar();
      seguir();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        toast.info("Ya hay una actualización en curso. Te avisamos cuando termine.");
        seguir();
      } else {
        toast.error(mensajeDeError(err, "No se pudo iniciar la actualización"));
      }
    } finally {
      setLanzando(false);
    }
  }, [seguir]);

  // Solo lo que esta pantalla está siguiendo: un `enCurso` colgado en la base
  // no bloquea el botón (ver MAX_POLLS).
  const enCurso = siguiendo || lanzando;
  return { estado, enCurso, lanzando, actualizar };
}
