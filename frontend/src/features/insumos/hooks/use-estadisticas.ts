"use client";

import { useEffect, useState } from "react";
import { insumosApi } from "../api/insumos-api";
import { ApiError } from "@/services/http-client";
import type { CustomerDetailResponse, EstadisticasFilters, EstadisticasResponse } from "../types";

/** Carga de las dos pantallas de Estadísticas. Son de solo lectura: alcanza con
 * `useState` + `useEffect` (el proyecto no tiene librería de fetching).
 *
 * `loading` NO es un estado propio: se **deriva** comparando la clave del
 * pedido en curso contra la del último resultado guardado. Así el efecto no
 * llama a `setState` de forma síncrona (regla `react-hooks/set-state-in-effect`)
 * y, de paso, una respuesta vieja que llega tarde no puede pisar a una nueva:
 * su clave ya no coincide. El flag `cancelled` cubre el desmontaje.
 *
 * El error se devuelve como texto y lo pinta la pantalla en un card: son fallas
 * de pantalla completa (sin datos no hay nada que mostrar), no acciones
 * puntuales — un toast que se autodescarta escondería el motivo.
 */

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface Resolved<T> {
  key: string;
  data: T | null;
  error: string | null;
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return "No se pudo contactar al servidor.";
}

function filtersKey({ days, startDate, endDate }: EstadisticasFilters): string {
  return `${days ?? ""}|${startDate ?? ""}|${endDate ?? ""}`;
}

function stateFor<T>(resolved: Resolved<T> | null, key: string): AsyncState<T> {
  if (!resolved || resolved.key !== key) return { data: null, loading: true, error: null };
  return { data: resolved.data, loading: false, error: resolved.error };
}

export function useEstadisticas(filters: EstadisticasFilters): AsyncState<EstadisticasResponse> {
  const [resolved, setResolved] = useState<Resolved<EstadisticasResponse> | null>(null);
  const { days, startDate, endDate } = filters;
  const key = filtersKey(filters);

  useEffect(() => {
    let cancelled = false;
    insumosApi
      .getEstadisticas({ days, startDate, endDate })
      .then((data) => {
        if (!cancelled) setResolved({ key, data, error: null });
      })
      .catch((error: unknown) => {
        if (!cancelled) setResolved({ key, data: null, error: errorMessage(error) });
      });
    return () => {
      cancelled = true;
    };
  }, [key, days, startDate, endDate]);

  return stateFor(resolved, key);
}

/** `customerId === null` = el `[id]` de la ruta no es un número: no se le pega
 * al backend, se devuelve el error directamente. */
export function useEstadisticasCliente(
  customerId: number | null,
  filters: EstadisticasFilters,
): AsyncState<CustomerDetailResponse> {
  const [resolved, setResolved] = useState<Resolved<CustomerDetailResponse> | null>(null);
  const { days, startDate, endDate } = filters;
  const key = `${customerId ?? ""}|${filtersKey(filters)}`;

  useEffect(() => {
    if (customerId === null) return;
    let cancelled = false;
    insumosApi
      .getEstadisticasCliente(customerId, { days, startDate, endDate })
      .then((data) => {
        if (!cancelled) setResolved({ key, data, error: null });
      })
      .catch((error: unknown) => {
        if (!cancelled) setResolved({ key, data: null, error: errorMessage(error) });
      });
    return () => {
      cancelled = true;
    };
  }, [key, customerId, days, startDate, endDate]);

  if (customerId === null) {
    return { data: null, loading: false, error: "El identificador de cliente no es válido." };
  }
  return stateFor(resolved, key);
}
