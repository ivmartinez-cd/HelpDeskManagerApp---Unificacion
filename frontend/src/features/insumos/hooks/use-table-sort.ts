"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/** Estado de orden de una tabla, con persistencia opcional en `localStorage`
 * (el legacy guardaba el orden elegido por el operario y lo restauraba al
 * volver a entrar — `useSortableTable` de SDSInsumos).
 *
 * El hook maneja SOLO el estado: ordenar la lista es responsabilidad del
 * componente, con su propio `useMemo`. Así no hay que memoizar comparadores
 * ni preocuparse por closures viejas, y cada tabla decide cómo extrae el valor
 * de cada columna.
 *
 * `localStorage` se lee recién en un `useEffect` (nunca durante el render):
 * el primer render tiene que ser idéntico en servidor y cliente o Next tira
 * error de hidratación.
 */

export type SortDirection = "asc" | "desc";

export interface SortState<K extends string> {
  key: K;
  direction: SortDirection;
}

interface UseTableSortOptions<K extends string> {
  /** Orden inicial, y el que se usa si lo guardado no es válido. */
  initial: SortState<K>;
  /** Claves aceptadas — lo que venga de `localStorage` se valida contra esto. */
  keys: readonly K[];
  /** Clave de `localStorage`. Omitir para no persistir. */
  storageKey?: string;
  /** Columnas que arrancan descendentes al clickearlas por primera vez
   * (fechas: lo más reciente arriba es lo que espera el operario). */
  descFirstKeys?: readonly K[];
}

function readStoredSort<K extends string>(
  storageKey: string,
  keys: readonly K[],
): SortState<K> | null {
  // Cualquier problema (JSON corrupto, clave de una versión anterior de la
  // tabla, storage bloqueado por el navegador) cae en el orden por default:
  // no es un error que valga la pena mostrarle al usuario.
  try {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null) return null;
    const { key, direction } = parsed as { key?: unknown; direction?: unknown };
    if (typeof key !== "string" || !keys.includes(key as K)) return null;
    if (direction !== "asc" && direction !== "desc") return null;
    return { key: key as K, direction };
  } catch {
    return null;
  }
}

export function useTableSort<K extends string>({
  initial,
  keys,
  storageKey,
  descFirstKeys,
}: UseTableSortOptions<K>) {
  const [sort, setSort] = useState<SortState<K>>(initial);

  // Se guardan en refs para que el efecto de hidratación y `toggleSort` no
  // dependan de la identidad de arrays literales creados en cada render del
  // componente que llama. La sincronización va en un efecto (nunca durante el
  // render) y este efecto está declarado ANTES del de hidratación, así que ya
  // corrió cuando aquel lee `keysRef.current`.
  const keysRef = useRef(keys);
  const descFirstRef = useRef(descFirstKeys);
  useEffect(() => {
    keysRef.current = keys;
    descFirstRef.current = descFirstKeys;
  }, [keys, descFirstKeys]);

  useEffect(() => {
    if (!storageKey) return;
    const stored = readStoredSort(storageKey, keysRef.current);
    if (stored) setSort(stored);
  }, [storageKey]);

  const toggleSort = useCallback(
    (key: K) => {
      setSort((prev) => {
        const next: SortState<K> =
          prev.key === key
            ? { key, direction: prev.direction === "asc" ? "desc" : "asc" }
            : { key, direction: descFirstRef.current?.includes(key) ? "desc" : "asc" };
        if (storageKey) {
          try {
            window.localStorage.setItem(storageKey, JSON.stringify(next));
          } catch {
            // Storage lleno o deshabilitado: el orden igual se aplica en memoria.
          }
        }
        return next;
      });
    },
    [storageKey],
  );

  return { sort, toggleSort };
}

export type SortValue = string | number | null | undefined;

/** Comparador genérico para el `useMemo` de ordenamiento. Los valores vacíos
 * quedan SIEMPRE al final, independientemente de la dirección: una fila sin
 * fecha de descubrimiento no debería encabezar la tabla al invertir el orden. */
export function compareSortValues(a: SortValue, b: SortValue, direction: SortDirection): number {
  const factor = direction === "asc" ? 1 : -1;
  const aEmpty = a === null || a === undefined || a === "";
  const bEmpty = b === null || b === undefined || b === "";
  if (aEmpty && bEmpty) return 0;
  if (aEmpty) return 1;
  if (bEmpty) return -1;
  if (typeof a === "number" && typeof b === "number") return (a - b) * factor;
  return (
    String(a).localeCompare(String(b), "es-AR", { numeric: true, sensitivity: "base" }) * factor
  );
}
