"use client";

import { useCallback, useMemo } from "react";
import {
  advertenciasDeOperadores,
  diaInicialVigente,
  diaSemanaDeIso,
  diasActivosDeRango,
  erroresDeFranjas,
  franjasSinOperador,
  huecosDeCobertura,
} from "../lib/variante-validacion";
import { formatDiaMes, hoyIso } from "../lib/variante-estado";
import type { AdvertenciaCobertura, FranjaEditable } from "../types/grilla-variantes";
import type { Casilla, Slot, UserOption } from "../types/turnos";

interface Args {
  casillas: Casilla[];
  titular: Slot[];
  users: UserOption[];
  franjas: FranjaEditable[];
  ausencias: AdvertenciaCobertura[];
  desde: string;
  hasta: string;
  /** Pestaña de día que el usuario eligió; puede quedar fuera del rango. */
  diaElegido: number;
}

/** Todo lo que el editor de grilla de vacaciones deriva de su estado:
 * validaciones en vivo, días que el rango alcanza y qué se guarda. Vive acá
 * porque `variante-editor.tsx` ya rozaba el tamaño máximo de archivo (§4). */
export function useVarianteDerivados({
  casillas, titular, users, franjas, ausencias, desde, hasta, diaElegido,
}: Args) {
  const nombreCasilla = useCallback(
    (id: string) => casillas.find((c) => c.id === id)?.nombre ?? "?",
    [casillas],
  );
  const nombreUser = useCallback(
    (id: string) => users.find((u) => u.id === id)?.fullName ?? id,
    [users],
  );
  const ausenciaPorUser = useMemo(
    () => new Map(ausencias.filter((a) => a.userId).map((a) => [a.userId as string, a])),
    [ausencias],
  );
  const opcionesOperador = useMemo(
    () =>
      users.map((u) => {
        const aus = ausenciaPorUser.get(u.id);
        return {
          id: u.id,
          label: u.fullName,
          sublabel:
            aus && aus.desde && aus.hasta
              ? `vacaciones ${formatDiaMes(aus.desde)}–${formatDiaMes(aus.hasta)}`
              : undefined,
        };
      }),
    [users, ausenciaPorUser],
  );

  const errores = useMemo(() => erroresDeFranjas(franjas, nombreCasilla), [franjas, nombreCasilla]);
  const operadoresSolapados = useMemo(
    () => advertenciasDeOperadores(franjas, nombreCasilla, nombreUser),
    [franjas, nombreCasilla, nombreUser],
  );
  const diasActivos = useMemo(() => diasActivosDeRango(desde, hasta), [desde, hasta]);
  const huecos = useMemo(
    () => huecosDeCobertura(franjas, titular, diasActivos),
    [franjas, titular, diasActivos],
  );
  const sinOperador = useMemo(() => franjasSinOperador(franjas), [franjas]);
  const keysConError = useMemo(() => new Set(errores.flatMap((e) => e.keys)), [errores]);
  const rangoInvalido = Boolean(desde && hasta && hasta < desde);
  /** El día editado siempre tiene que ser uno que el rango alcance: "Ajustar
   * turnos de hoy" un martes abría en Lunes y lo editado ahí no se veía nunca
   * en Turnos del día. Se deriva en vez de corregirse por efecto para que
   * achicar el rango reubique la pestaña en el mismo render. */
  const diaActivo =
    !diasActivos || diasActivos.has(diaElegido)
      ? diaElegido
      : diaInicialVigente(diasActivos, diaSemanaDeIso(hoyIso()));
  /** Lo que realmente se guarda: si el rango se achicó después de precargar,
   * las franjas de días que ya no aplican no van al payload. */
  const franjasVigentes = useMemo(
    () => franjas.filter((f) => !diasActivos || diasActivos.has(f.diaSemana)),
    [franjas, diasActivos],
  );
  const puedeGuardar =
    Boolean(desde && hasta) && !rangoInvalido && franjasVigentes.length > 0 && errores.length === 0;

  return {
    nombreCasilla, nombreUser, opcionesOperador, errores, operadoresSolapados, diasActivos,
    huecos, sinOperador, keysConError, rangoInvalido, diaActivo, franjasVigentes, puedeGuardar,
  };
}
