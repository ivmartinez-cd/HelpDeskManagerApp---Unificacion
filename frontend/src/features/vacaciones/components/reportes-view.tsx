"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { BarChart3, FileSpreadsheet, FileText, Search } from "lucide-react";
import {
  BrandButton,
  BrandEmptyState,
  BrandSkeleton,
} from "@/shared/components/ui/brand-form";
import { reportesApi } from "../api/reportes-api";
import type { FilaEmpleadoReporte, ReporteVacaciones } from "../types/vacaciones";
import { ReportesAuditoriaTabs } from "./reportes-auditoria-tabs";

const ALTO_MAX_BARRA = 150;

function iniciales(nombre: string): string {
  return nombre
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0])
    .join("")
    .toUpperCase();
}

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

function GraficoSectores({ data }: { data: ReporteVacaciones }) {
  const hoy = new Date().toLocaleDateString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
  const max = Math.max(1, ...data.porSector.flatMap((s) => [s.used, s.available]));
  const alto = (v: number) => Math.round((v / max) * ALTO_MAX_BARRA);
  return (
    <div className="rounded-[12px] border border-border bg-card p-[22px]">
      <h3 className="font-heading text-sm font-bold text-foreground">
        Días consumidos vs. disponibles por sector
      </h3>
      <p className="mb-5 mt-1 font-body text-[12.5px] text-muted-foreground">
        Ciclo {data.year} — actualizado al {hoy}
      </p>
      <div className="mb-3.5 flex h-[180px] items-end justify-center gap-7 border-b border-border px-5">
        {data.porSector.map((s) => (
          <div key={s.nombre} className="flex flex-col items-center gap-1.5">
            <div className="flex h-40 items-end gap-1">
              <div className="flex flex-col items-center justify-end gap-0.5">
                <span className="font-body text-[10px] font-semibold text-[#F7941D]">
                  {s.used}
                </span>
                <div
                  className="w-[26px] rounded-t-[4px] bg-[#F7941D]"
                  style={{ height: `${alto(s.used)}px` }}
                />
              </div>
              <div className="flex flex-col items-center justify-end gap-0.5">
                <span className="font-body text-[10px] font-semibold text-muted-foreground">
                  {s.available}
                </span>
                <div
                  className="w-[26px] rounded-t-[4px] bg-muted"
                  style={{ height: `${alto(s.available)}px` }}
                />
              </div>
            </div>
            <span className="max-w-[80px] text-center font-body text-[11.5px] text-muted-foreground">
              {s.nombre}
            </span>
          </div>
        ))}
      </div>
      <div className="flex justify-center gap-[18px]">
        <div className="flex items-center gap-1.5">
          <div className="h-3 w-3 rounded-[3px] bg-[#F7941D]" />
          <span className="font-body text-[12.5px] text-muted-foreground">Consumidos</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-3 w-3 rounded-[3px] bg-muted" />
          <span className="font-body text-[12.5px] text-muted-foreground">Disponibles</span>
        </div>
      </div>
    </div>
  );
}

const TH = "px-3.5 py-2.5 text-right font-heading text-[10px] uppercase tracking-[.05em]";

function TablaEmpleados({
  filas,
  filtro,
  onFiltro,
}: {
  filas: FilaEmpleadoReporte[];
  filtro: string;
  onFiltro: (v: string) => void;
}) {
  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-card">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <h3 className="font-heading text-[13px] font-bold text-foreground">Por empleado</h3>
        <div className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Filtrar…"
            value={filtro}
            onChange={(e) => onFiltro(e.target.value)}
            className="w-40 rounded-[7px] border border-border bg-muted/30 py-1.5 pl-8 pr-3 font-body text-[12.5px] text-foreground outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-brand-orange/40"
          />
        </div>
      </div>
      <table className="w-full font-body text-[13px]">
        <thead>
          <tr className="border-b border-border bg-muted/30 text-muted-foreground">
            <th className={`${TH} text-left`}>Empleado</th>
            <th className={`${TH} text-[#F7941D]`}>Cons.</th>
            <th className={TH}>Pend.</th>
            <th className={TH}>Disp.</th>
          </tr>
        </thead>
        <tbody>
          {filas.map((f) => (
            <tr key={f.nombre} className="border-b border-border/60 last:border-0">
              <td className="px-3.5 py-2.5">
                <div className="flex items-center gap-2">
                  <div
                    className="flex h-[26px] w-[26px] flex-none items-center justify-center rounded-[6px] font-heading text-[9.5px] font-bold text-white"
                    style={{ backgroundColor: f.color }}
                  >
                    {iniciales(f.nombre)}
                  </div>
                  <span className="font-semibold text-foreground">{f.nombre}</span>
                </div>
              </td>
              <td className="px-3.5 py-2.5 text-right font-semibold text-[#F7941D]">
                {f.used}
              </td>
              <td className="px-3.5 py-2.5 text-right text-[#d97706]">{f.pending}</td>
              <td className="px-3.5 py-2.5 text-right font-semibold text-[#059669]">
                {f.available}
              </td>
            </tr>
          ))}
          {filas.length === 0 && (
            <tr>
              <td colSpan={4} className="px-3.5 py-4 text-center text-muted-foreground">
                Sin resultados para el filtro.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function TablaSectores({ data }: { data: ReporteVacaciones }) {
  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <h3 className="font-heading text-[13px] font-bold text-foreground">Por sector</h3>
      </div>
      <table className="w-full font-body text-[13px]">
        <thead>
          <tr className="border-b border-border bg-muted/30 text-muted-foreground">
            <th className={`${TH} text-left`}>Sector</th>
            <th className={TH}>Empl.</th>
            <th className={TH}>Anuales</th>
            <th className={`${TH} text-[#F7941D]`}>Cons.</th>
            <th className={TH}>Disp.</th>
          </tr>
        </thead>
        <tbody>
          {data.porSector.map((s) => (
            <tr key={s.nombre} className="border-b border-border/60 last:border-0">
              <td className="px-3.5 py-2.5">
                <div className="flex items-center gap-[7px]">
                  <div
                    className="h-2 w-2 flex-none rounded-full"
                    style={{ backgroundColor: s.color }}
                  />
                  <span className="font-semibold text-foreground">{s.nombre}</span>
                </div>
              </td>
              <td className="px-3.5 py-2.5 text-right text-muted-foreground">
                {s.empleados}
              </td>
              <td className="px-3.5 py-2.5 text-right text-muted-foreground">{s.annual}</td>
              <td className="px-3.5 py-2.5 text-right font-semibold text-[#F7941D]">
                {s.used}
              </td>
              <td className="px-3.5 py-2.5 text-right font-semibold text-[#059669]">
                {s.available}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
