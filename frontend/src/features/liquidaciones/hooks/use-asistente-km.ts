"use client";

import { useCallback, useRef, useState } from "react";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { DatosBandeja, FilaNoEncontrada } from "../lib/asistente-km-bandeja";
import type { EstadoAsistenteKm, SucursalSiges } from "../types/liquidaciones";

/** Estado de cada chequeo gratis que corre tras "Empezar" (no modifican la Tabla KM;
 * Georef/Nominatim solo escriben su cache). */
export type EstadoChequeo = "pendiente" | "corriendo" | "ok" | "error";

export interface ProgresoChequeos {
  lectura: EstadoChequeo;
  georef: EstadoChequeo;
  nominatim: EstadoChequeo;
  /** Lo que quedó sin chequear por el tope interno de cada servicio gratis. */
  pendientesPorTope: number;
}

const PROGRESO_INICIAL: ProgresoChequeos = {
  lectura: "pendiente", georef: "pendiente", nominatim: "pendiente", pendientesPorTope: 0,
};

export interface DatosAsistente {
  estado: EstadoAsistenteKm;
  bandeja: DatosBandeja;
  sucursalesSiges: SucursalSiges[];
}

async function leerTodo(prestadorId: string, noEncontradas: FilaNoEncontrada[] | null): Promise<DatosAsistente> {
  const [estado, propuestas, coordenadas, tier0, tier1, tier1b, worklist, pines, sucursalesSiges] = await Promise.all([
    liquidacionesApi.estadoAsistenteKm(prestadorId),
    liquidacionesApi.listPropuestasN2(prestadorId),
    liquidacionesApi.listCoordenadas(prestadorId),
    liquidacionesApi.listGeovalidacionTier0(prestadorId),
    liquidacionesApi.listGeovalidacionTier1(prestadorId),
    liquidacionesApi.listGeovalidacionTier1b(prestadorId),
    liquidacionesApi.getWorklistTier2(prestadorId).catch(() => null),
    liquidacionesApi.listPinesSospechosos(prestadorId),
    liquidacionesApi.listarTodasSucursalesSiges(prestadorId),
  ]);
  return {
    estado,
    sucursalesSiges,
    bandeja: { estado, propuestas, coordenadas, tier0, tier1, tier1b, worklist, pines, noEncontradas },
  };
}

/** Lectura compuesta en frontend (decisión 0.4.d del rediseño): los mismos GET que
 * el wizard viejo disparaba repartidos por paso, ahora juntos. */
export function useAsistenteKm(prestadorId: string) {
  const [datos, setDatos] = useState<DatosAsistente | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progreso, setProgreso] = useState<ProgresoChequeos>(PROGRESO_INICIAL);
  const noEncontradasRef = useRef<FilaNoEncontrada[] | null>(null);

  const recargar = useCallback(async () => {
    try {
      setDatos(await leerTodo(prestadorId, noEncontradasRef.current));
      setError(null);
    } catch {
      setError("No se pudo leer el estado del asistente. Cerrá y volvé a abrir.");
    }
  }, [prestadorId]);

  /** Guarda la lista de filas que Gestión no encontró (la devuelve el refresco) para
   * que la bandeja pueda mostrarlas como "nombre sin candidato". */
  const registrarNoEncontradas = useCallback((filas: FilaNoEncontrada[]) => {
    noEncontradasRef.current = filas;
  }, []);

  const avanzar = (parcial: Partial<ProgresoChequeos>) => setProgreso((p) => ({ ...p, ...parcial }));

  /** Chequeos que no modifican filas: lectura + provincia del pin con datos oficiales
   * + segunda opinión. Cada uno falla por separado sin frenar a los demás. */
  const correrChequeosGratis = useCallback(async () => {
    setProgreso({ ...PROGRESO_INICIAL, lectura: "corriendo" });
    let pendientes = 0;
    await recargar();
    avanzar({ lectura: "ok", georef: "corriendo" });
    try {
      pendientes += (await liquidacionesApi.consultarGeoref(prestadorId)).pendientesPorTope;
      avanzar({ georef: "ok" });
    } catch { avanzar({ georef: "error" }); }
    avanzar({ nominatim: "corriendo" });
    try {
      pendientes += (await liquidacionesApi.consultarNominatim(prestadorId)).pendientesPorTope;
      avanzar({ nominatim: "ok" });
    } catch { avanzar({ nominatim: "error" }); }
    await recargar();
    avanzar({ pendientesPorTope: pendientes });
  }, [prestadorId, recargar]);

  return { datos, error, progreso, recargar, correrChequeosGratis, registrarNoEncontradas };
}
