"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type SortDirection = "asc" | "desc";

export interface SortState<K extends string> {
  key: K;
  direction: SortDirection;
}

interface UseTableSortOptions<K extends string> {
  initial: SortState<K>;
  keys: readonly K[];
  storageKey?: string;
  descFirstKeys?: readonly K[];
}

function readStoredSort<K extends string>(
  storageKey: string,
  keys: readonly K[],
): SortState<K> | null {
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
