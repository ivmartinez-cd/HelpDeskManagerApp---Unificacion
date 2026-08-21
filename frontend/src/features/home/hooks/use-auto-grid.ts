"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { elegirColumnas, repartoParejo, type GridLayout } from "../utils/grid-packing";

export const GRID_GAP = 12;

export interface AutoGridState extends GridLayout {
  /** false hasta la primera medición real (el grid se dibuja oculto mientras). */
  medido: boolean;
}

interface Estado {
  w: number;
  h: number;
  items: Map<Element, { index: number; height: number }>;
  floorK: number;
  cols: number;
  key: string;
}

/** Grid auto-ajustable: observa el alto disponible del contenedor y el alto
 * real de cada card, y elige (vía `elegirColumnas`) cuántas columnas usar
 * para que todo entre sin scroll. Toda la lógica corre en los callbacks de
 * ResizeObserver; solo el layout elegido es estado de React. */
export function useAutoGrid(count: number) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [layout, setLayout] = useState<AutoGridState>({
    cols: 1,
    sizes: [count],
    fits: true,
    medido: false,
  });
  const estado = useRef<Estado>({ w: 0, h: 0, items: new Map(), floorK: 1, cols: 1, key: "" });
  const observer = useRef<ResizeObserver | null>(null);

  const recompute = useCallback(() => {
      const e = estado.current;
      const heights: number[] = [];
      for (const { index, height } of e.items.values()) heights[index] = height;
      for (let i = 0; i < heights.length; i++) heights[i] ??= 0;
      const { layout: next, floorK } = elegirColumnas({
        heights,
        ancho: e.w,
        alto: e.h,
        gap: GRID_GAP,
        floorK: e.floorK,
        colsActual: e.cols,
      });
      e.floorK = floorK;
      const key = `${next.cols}|${next.sizes.join(",")}|${next.fits}`;
      if (key === e.key) return;
      e.key = key;
      e.cols = next.cols;
      setLayout({ ...next, medido: true });
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      const e = estado.current;
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (entry.target === el) {
          if (width !== e.w || height !== e.h) e.floorK = 1;
          e.w = width;
          e.h = height;
        } else {
          const item = e.items.get(entry.target);
          if (item) item.height = height;
        }
      }
      recompute();
    });
    observer.current = ro;
    ro.observe(el);
    // Los ref callbacks de las cards corren antes que este efecto en el
    // primer montaje: observar lo que ya se registró.
    for (const node of estado.current.items.keys()) ro.observe(node);
    return () => {
      ro.disconnect();
      observer.current = null;
    };
  }, [recompute]);

  // Un ref callback estable por posición: registra/desregistra la card en el
  // observer. Cambiar el conjunto de cards (pestaña) resetea la histéresis.
  const itemRefs = useMemo(
    () =>
      Array.from({ length: count }, (_, index) => (el: HTMLElement | null) => {
        const e = estado.current;
        if (el) {
          e.items.set(el, { index, height: 0 });
          observer.current?.observe(el);
        } else {
          for (const [node, item] of e.items) {
            if (item.index !== index) continue;
            observer.current?.unobserve(node);
            e.items.delete(node);
          }
        }
        e.floorK = 1;
      }),
    [count],
  );

  const total = layout.sizes.reduce((a, b) => a + b, 0);
  const sizes = total === count ? layout.sizes : repartoParejo(count, layout.cols);
  return { containerRef, itemRefs, layout: { ...layout, sizes, cols: sizes.length } };
}
