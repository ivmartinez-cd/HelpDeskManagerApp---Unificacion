"use client";

import { useMemo } from "react";
import { useTheme } from "@/shared/components/theme-provider";

/** Colores de Chart.js leídos de los tokens del tema (globals.css): el canvas
 * no entiende `var(--x)`. Se recalculan al cambiar de tema; `setTheme` aplica
 * la clase antes del re-render, así que el valor computado ya es el nuevo. */
export interface TemaGrafico {
  texto: string;
  grilla: string;
  fondo: string;
}

function leerTema(): TemaGrafico {
  if (typeof document === "undefined") return { texto: "#8a8a8a", grilla: "#dddddd", fondo: "#ffffff" };
  const estilos = getComputedStyle(document.documentElement);
  const leer = (nombre: string, respaldo: string) => estilos.getPropertyValue(nombre).trim() || respaldo;
  return {
    texto: leer("--chart-tick", "#8a8a8a"),
    grilla: leer("--chart-grid", "#dddddd"),
    fondo: leer("--card", "#ffffff"),
  };
}

/** Colores fijos de papel para el PDF: no dependen del tema de la app. */
export const TEMA_CLARO: TemaGrafico = { texto: "#58595B", grilla: "#e5e5e5", fondo: "#ffffff" };

/** Con `claro` devuelve siempre `TEMA_CLARO` (reporte imprimible). */
export function useTemaGrafico(claro = false): TemaGrafico {
  const { resolvedTheme } = useTheme();
  // eslint-disable-next-line react-hooks/exhaustive-deps -- resolvedTheme dispara la relectura
  const delTema = useMemo(() => leerTema(), [resolvedTheme]);
  return claro ? TEMA_CLARO : delTema;
}
