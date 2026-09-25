"use client";

import type { DimensionFiltro, Reporte } from "../../../types/reporte";
import { BarrasHorizontales } from "./barras-horizontales";
import { SinDatos, TarjetaGrafico } from "./tarjeta-grafico";
import { NARANJA, recortarAlMedio } from "./utilidades";

const TOPE = 6;
const MAX_CARACTERES = 26;

interface Props {
  reporte: Reporte;
  onFiltrar?: (dimension: DimensionFiltro, valor: string) => void;
  alto?: number;
  /** Colores de papel fijos (PDF), sin importar el tema. */
  claro?: boolean;
}

const recortar = (nombre: string) => recortarAlMedio(nombre, MAX_CARACTERES);

/** Top 6 sucursales del período completo (port de `SucursalBar`). Los nombres
 * largos se recortan por el medio; el completo queda en el tooltip. */
export function GraficoSucursales({ reporte, onFiltrar, claro, alto = 240 }: Props) {
  const barras = reporte.sucursales.slice(0, TOPE).map((s) => ({
    nombre: s.nombre,
    cantidad: s.cantidad,
    color: NARANJA,
  }));

  return (
    <TarjetaGrafico titulo="Incidentes por sucursal" subtitulo="Período completo" derecha={`Top ${barras.length}`}>
      {barras.length === 0 ? (
        <SinDatos />
      ) : (
        <BarrasHorizontales
          barras={barras}
          activa={reporte.filtros.sucursal}
          alto={alto}
          grosor={18}
          etiqueta={recortar}
          claro={claro}
          onClick={onFiltrar && ((nombre) => onFiltrar("sucursal", nombre))}
        />
      )}
    </TarjetaGrafico>
  );
}
