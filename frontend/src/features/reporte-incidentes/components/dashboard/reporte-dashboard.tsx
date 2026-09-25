"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useReporte } from "../../hooks/use-reporte";
import { RUTA_SELECCION } from "../../lib/url-reporte";
import { EncabezadoReporte } from "./encabezado-reporte";
import { BarraReporte } from "./barra-reporte";
import { FiltrosActivos } from "./filtros-activos";
import { KpisReporte } from "./kpis-reporte";
import { OportunidadesMejora } from "./oportunidades-mejora";
import { GraficosReporte } from "./graficos-reporte";
import { TablaIncidentes } from "../tabla/tabla-incidentes";
import { PanelPendientes } from "../tabla/panel-pendientes";
import { TipificacionIA } from "../tabla/tipificacion-ia";

/** Dashboard del reporte (port de `app/dashboard/page.tsx` del legacy), de
 * arriba abajo en el mismo orden. KPIs, evolución y tabla siguen los filtros;
 * gráficos y oportunidades muestran el período completo (navegan). */
export function ReporteDashboard() {
  const estado = useReporte();
  const router = useRouter();

  useEffect(() => {
    if (estado.sinCliente) router.replace(RUTA_SELECCION);
  }, [estado.sinCliente, router]);

  if (estado.error) {
    return (
      <div className="flex flex-col items-start gap-3 p-6">
        <p className="font-body text-sm text-destructive">{estado.error}</p>
        <Link href={RUTA_SELECCION} className="font-body text-sm text-brand-orange underline">
          Elegir otro cliente
        </Link>
      </div>
    );
  }

  const { reporte } = estado;
  return (
    <div className="flex flex-col gap-5 p-4 md:p-6" aria-busy={estado.cargando || estado.navegando || estado.actualizando}>
      <EncabezadoReporte estado={estado} />
      <BarraReporte estado={estado} />
      {reporte && (
        <>
          <FiltrosActivos estado={estado} />
          <KpisReporte reporte={reporte} />
          <OportunidadesMejora reporte={reporte} onFiltrar={estado.alternarFiltro} />
          <GraficosReporte reporte={reporte} filtros={estado.filtros} onFiltrar={estado.alternarFiltro} />
          <TablaIncidentes estado={estado} />
          <PanelPendientes estado={estado} />
          <p className="text-center font-body text-xs text-muted-foreground">
            Generado {new Date(reporte.generado_en).toLocaleString("es-AR")} · Canal Directo ·
            Confidencial — Uso exclusivo del Directorio
          </p>
          <TipificacionIA estado={estado} />
        </>
      )}
    </div>
  );
}
