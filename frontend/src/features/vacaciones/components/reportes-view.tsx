"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { BarChart3, FileSpreadsheet, FileText } from "lucide-react";
import {
  BrandButton,
  BrandEmptyState,
  BrandSkeleton,
} from "@/shared/components/ui/brand-form";
import { reportesApi } from "../api/reportes-api";
import type { FilaEmpleadoReporte, ReporteVacaciones } from "../types/vacaciones";
import { ReportesAuditoriaTabs } from "./reportes-auditoria-tabs";
import { GraficoSectores } from "./reportes-grafico-sectores";
import { TablaEmpleados, TablaSectores } from "./reportes-tablas";

export function ReportesView() {
  const [data, setData] = useState<ReporteVacaciones | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [descargando, setDescargando] = useState<"excel" | "pdf" | null>(null);
  const [filtro, setFiltro] = useState("");

  const load = useCallback(() => {
    reportesApi
      .getReporte()
      .then((r) => {
        setData(r);
        setError(null);
      })
      .catch((err: unknown) => {
        console.error("Error al cargar el reporte:", err);
        setError("No se pudo cargar el reporte de vacaciones.");
      });
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const empleadosFiltrados = useMemo<FilaEmpleadoReporte[]>(() => {
    if (data === null) return [];
    const q = filtro.trim().toLowerCase();
    if (!q) return data.porEmpleado;
    return data.porEmpleado.filter((f) => f.nombre.toLowerCase().includes(q));
  }, [data, filtro]);

  async function descargar(tipo: "excel" | "pdf") {
    setDescargando(tipo);
    try {
      await (tipo === "excel" ? reportesApi.downloadExcel() : reportesApi.downloadPdf());
    } catch (err: unknown) {
      console.error("Error al exportar el reporte:", err);
      setError(`No se pudo exportar el reporte a ${tipo === "excel" ? "Excel" : "PDF"}.`);
    } finally {
      setDescargando(null);
    }
  }

  const year = data?.year ?? new Date().getFullYear();

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
            Reportes
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Vacaciones · Ciclo {year}
          </p>
        </div>
        <div className="flex gap-2 pt-1">
          <BrandButton
            variant="outline"
            size="sm"
            loading={descargando === "excel"}
            onClick={() => descargar("excel")}
          >
            <FileSpreadsheet className="h-4 w-4" /> Excel
          </BrandButton>
          <BrandButton
            variant="outline"
            size="sm"
            loading={descargando === "pdf"}
            onClick={() => descargar("pdf")}
          >
            <FileText className="h-4 w-4" /> PDF
          </BrandButton>
        </div>
      </div>

      <ReportesAuditoriaTabs />

      {error && (
        <div className="flex items-center justify-between gap-4 rounded-[12px] border border-destructive/20 bg-destructive/10 px-5 py-4">
          <p className="font-body text-sm text-foreground">{error}</p>
          <BrandButton variant="outline" size="sm" onClick={load}>
            Reintentar
          </BrandButton>
        </div>
      )}

      {data === null && !error && (
        <div className="flex flex-col gap-4">
          <BrandSkeleton className="h-64 w-full" />
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <BrandSkeleton className="h-48 w-full" />
            <BrandSkeleton className="h-48 w-full" />
          </div>
        </div>
      )}

      {data !== null && data.porEmpleado.length === 0 && (
        <BrandEmptyState
          icon={BarChart3}
          title="Sin datos para reportar"
          description="Cuando haya empleados con ciclos de vacaciones, el reporte va a aparecer acá."
        />
      )}

      {data !== null && data.porEmpleado.length > 0 && (
        <>
          <GraficoSectores data={data} />
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <TablaEmpleados filas={empleadosFiltrados} filtro={filtro} onFiltro={setFiltro} />
            <TablaSectores data={data} />
          </div>
        </>
      )}
    </div>
  );
}
