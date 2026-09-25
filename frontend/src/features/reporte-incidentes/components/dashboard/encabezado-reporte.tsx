"use client";

import Link from "next/link";
import { ArrowLeftRight } from "lucide-react";
import type { EstadoDashboard } from "../../hooks/use-reporte";
import { RUTA_SELECCION } from "../../lib/url-reporte";
import { BotonCategorias } from "../categorias/boton-categorias";
import { BotonExportarPdf } from "../imprimible/boton-exportar-pdf";

/** Título con el rango, cliente con "Cambiar" y, a la derecha, las acciones
 * (Categorías solo para quien puede editar; Exportar PDF para todos). */
export function EncabezadoReporte({ estado }: { estado: EstadoDashboard }) {
  const { reporte } = estado;
  return (
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="flex min-w-0 flex-col gap-1.5">
        <h1 className="font-heading text-[25px] font-extrabold text-foreground">
          Reporte de incidentes{reporte ? ` · ${reporte.rango_etiqueta}` : ""}
        </h1>
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 font-body text-sm">
          <span className="font-bold text-foreground">{reporte?.empresa.nombre ?? "Cargando cliente…"}</span>
          {reporte && <span className="text-xs text-muted-foreground">ID {reporte.empresa.id}</span>}
          <Link
            href={RUTA_SELECCION}
            className="inline-flex items-center gap-1 text-[13px] font-semibold text-brand-orange hover:underline"
          >
            <ArrowLeftRight className="h-3.5 w-3.5" aria-hidden="true" />
            Cambiar
          </Link>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {estado.canUpdate && <BotonCategorias estado={estado} />}
        <BotonExportarPdf estado={estado} />
      </div>
    </div>
  );
}
