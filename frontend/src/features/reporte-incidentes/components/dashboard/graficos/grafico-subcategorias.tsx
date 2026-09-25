"use client";

import type { DimensionFiltro, Reporte } from "../../../types/reporte";
import { BarrasHorizontales } from "./barras-horizontales";
import { SinDatos, TarjetaGrafico } from "./tarjeta-grafico";
import { colorCategoria } from "./utilidades";

const TOPE = 10;
const MAX_CARACTERES = 26;

interface Props {
  reporte: Reporte;
  onFiltrar?: (dimension: DimensionFiltro, valor: string) => void;
  alto?: number;
  /** Colores de papel fijos (PDF), sin importar el tema. */
  claro?: boolean;
}

const recortarFinal = (nombre: string) =>
  nombre.length > MAX_CARACTERES ? `${nombre.slice(0, MAX_CARACTERES - 1).trimEnd()}…` : nombre;

/** Top 10 subcategorías del período completo, con el color de su categoría
 * (port de `SubcategoryBar`). */
export function GraficoSubcategorias({ reporte, onFiltrar, claro, alto = 320 }: Props) {
  const barras = reporte.subcategorias.slice(0, TOPE).map((s) => ({
    nombre: s.nombre,
    cantidad: s.cantidad,
    color: colorCategoria(reporte, s.categoria),
    detalle: `Categoría: ${s.categoria}`,
  }));

  return (
    <TarjetaGrafico
      titulo="Incidentes por subcategoría"
      subtitulo="Color de su categoría"
      derecha={`Top ${barras.length}`}
    >
      {barras.length === 0 ? (
        <SinDatos />
      ) : (
        <BarrasHorizontales
          barras={barras}
          activa={reporte.filtros.subcategoria}
          alto={alto}
          grosor={14}
          etiqueta={recortarFinal}
          claro={claro}
          onClick={onFiltrar && ((nombre) => onFiltrar("subcategoria", nombre))}
        />
      )}
    </TarjetaGrafico>
  );
}
