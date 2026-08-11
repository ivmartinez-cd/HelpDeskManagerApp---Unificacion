"use client";

import { useEffect, useState } from "react";
import { insumosApi } from "../api/insumos-api";
import type {
  AvailabilityWindow,
  ConsumableDetail,
  ConsumableHistoryPoint,
  ConsumableRequestHistoryItem,
  DeviceSupplyItem,
  RequestRow,
} from "../types";

/** Las 5 lecturas que dispara el modal de detalle de consumible, en paralelo.
 *
 * Cada fuente tiene su propio estado de carga/error porque son independientes:
 * `/detail` tira 404 legítimo cuando el consumible ya no existe en Insight, y
 * eso no puede tumbar el gráfico ni las tablas. Si la solicitud no trae
 * `consumableIndex` (Insight no lo devolvió en la última lectura), las tres
 * consultas por consumible se saltean directamente.
 *
 * El hook NO resetea su estado cuando cambia la fila: el modal que lo consume
 * se monta con `key={row.requestId}`, así que abrir otro consumible arranca
 * una instancia limpia. Eso evita el patrón "setState sincrónico dentro de un
 * efecto" para volver todo a cero en cada apertura.
 */

const SUPPLIES_LIMIT = 10;

interface Source<T> {
  data: T;
  loading: boolean;
  error: string | null;
}

export interface ConsumableDetailState {
  history: Source<ConsumableHistoryPoint[]>;
  requests: Source<ConsumableRequestHistoryItem[]>;
  detail: Source<ConsumableDetail | null>;
  windows: AvailabilityWindow[];
  supplies: Source<DeviceSupplyItem[]>;
}

function pending<T>(data: T, loading: boolean): Source<T> {
  return { data, loading, error: null };
}

function message(error: unknown): string {
  return error instanceof Error ? error.message : "Error desconocido";
}

export function useConsumableDetail(row: RequestRow | null): ConsumableDetailState {
  const requestId = row?.requestId ?? null;
  const deviceId = row?.deviceId ?? null;
  const serial = row?.serial ?? null;
  const consumableIndex = row?.consumableIndex ?? null;
  const customerId = row?.customerId ?? null;
  const hasConsumable = consumableIndex !== null && deviceId !== null;

  const [history, setHistory] = useState<Source<ConsumableHistoryPoint[]>>(() =>
    pending([], hasConsumable),
  );
  const [requests, setRequests] = useState<Source<ConsumableRequestHistoryItem[]>>(() =>
    pending([], hasConsumable && customerId !== null),
  );
  const [detail, setDetail] = useState<Source<ConsumableDetail | null>>(() =>
    pending(null, hasConsumable),
  );
  const [windows, setWindows] = useState<AvailabilityWindow[]>([]);
  const [supplies, setSupplies] = useState<Source<DeviceSupplyItem[]>>(() =>
    pending([], serial !== null),
  );

  useEffect(() => {
    if (requestId === null || deviceId === null || serial === null) return;
    // `cancelled` reemplaza al AbortController del legacy: alcanza con ignorar
    // la respuesta vieja si el operador abre el detalle de otra fila antes de
    // que resuelva (el backend no cobra por la lectura, es cache/SOAP read-only).
    let cancelled = false;

    if (consumableIndex !== null) {
      void insumosApi
        .getConsumableHistory(deviceId, consumableIndex)
        .then((response) => {
          if (!cancelled) setHistory({ data: response.points, loading: false, error: null });
        })
        .catch((error: unknown) => {
          if (!cancelled) setHistory({ data: [], loading: false, error: message(error) });
        });

      void insumosApi
        .getConsumableDetail(deviceId, consumableIndex)
        .then((response) => {
          if (!cancelled) setDetail({ data: response, loading: false, error: null });
        })
        .catch((error: unknown) => {
          if (!cancelled) setDetail({ data: null, loading: false, error: message(error) });
        });

      if (customerId !== null) {
        void insumosApi
          .getConsumableRequestHistory(deviceId, consumableIndex, customerId)
          .then((response) => {
            if (!cancelled) setRequests({ data: response.items, loading: false, error: null });
          })
          .catch((error: unknown) => {
            if (!cancelled) setRequests({ data: [], loading: false, error: message(error) });
          });
      }
    }

    void insumosApi
      .getDeviceAvailabilityWindows(deviceId)
      .then((response) => {
        if (!cancelled) setWindows(response.windows);
      })
      .catch(() => {
        // Las ventanas "sin contacto" son contexto opcional del gráfico: si
        // fallan se omite la franja, no se muestra un error al operador.
        if (!cancelled) setWindows([]);
      });

    void insumosApi
      .getDeviceSupplies(serial, { limit: SUPPLIES_LIMIT })
      .then((response) => {
        if (!cancelled) setSupplies({ data: response.supplies, loading: false, error: null });
      })
      .catch((error: unknown) => {
        if (!cancelled) setSupplies({ data: [], loading: false, error: message(error) });
      });

    return () => {
      cancelled = true;
    };
  }, [requestId, deviceId, serial, consumableIndex, customerId]);

  return { history, requests, detail, windows, supplies };
}
