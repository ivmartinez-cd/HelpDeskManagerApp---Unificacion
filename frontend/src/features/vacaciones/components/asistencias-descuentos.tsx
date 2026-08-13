"use client";

import { useEffect, useMemo, useState } from "react";
import { BarChart3 } from "lucide-react";
import { ApiError } from "@/services/http-client";
import {
  BrandEmptyState,
  BrandSelect,
  BrandSkeleton,
} from "@/shared/components/ui/brand-form";
import { asistenciasApi } from "../api/asistencias-api";
import { gestionApi } from "../api/gestion-api";
import { iniciales } from "../lib/fechas";
import type { DescuentoRow, Sector } from "../types/vacaciones";

const MESES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

function detalle(r: DescuentoRow): string {
  const partes: string[] = [];
  if (r.diasDescontados > 0) partes.push(`${r.diasDescontados} desc.`);
  if (r.diasEnfermedad > 0) partes.push(`${r.diasEnfermedad} enf.`);
  if (r.guardias > 0) partes.push(`${r.guardias} guardia${r.guardias === 1 ? "" : "s"}`);
  return partes.length > 0 ? partes.join(" + ") : "Sin bajas";
}

export function AsistenciasDescuentos({ esAdmin }: { esAdmin: boolean }) {
  const hoy = new Date();
  const [mes, setMes] = useState(hoy.getMonth() + 1);
  const [anio, setAnio] = useState(hoy.getFullYear());
  const [sectores, setSectores] = useState<Sector[]>([]);
  const [sectorId, setSectorId] = useState("");
  const [filas, setFilas] = useState<DescuentoRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const anios = useMemo(() => {
    const desde = 2017;
    const hasta = hoy.getFullYear() + 2;
    return Array.from({ length: hasta - desde + 1 }, (_, i) => desde + i);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!esAdmin) return;
    gestionApi
      .listSectores()
      .then((secs) => {
        setSectores(secs);
        const tecnico = secs.find((s) =>
          ["técnico", "tecnico"].includes(s.name.toLowerCase()),
        );
        setSectorId((prev) => prev || (tecnico?.id ?? secs[0]?.id ?? ""));
      })
      .catch((err: unknown) => {
        console.error("Error al cargar sectores:", err);
      });
  }, [esAdmin]);

  useEffect(() => {
    let cancelado = false;
    asistenciasApi
      .reporteDescuentos(anio, mes, esAdmin && sectorId ? sectorId : undefined)
      .then((rows) => {
        if (cancelado) return;
        setFilas(rows);
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelado) return;
        setFilas([]);
        setError(
          err instanceof ApiError ? err.message : "No se pudo cargar el reporte.",
        );
      });
    return () => {
      cancelado = true;
    };
  }, [anio, mes, sectorId, esAdmin]);

  const sector = sectores.find((s) => s.id === sectorId);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h3 className="font-heading text-sm font-bold text-foreground">
          Días descontables por técnico · {MESES[mes - 1]} {anio}
          {sector ? ` · ${sector.name}` : ""}
        </h3>
        <div className="flex flex-wrap items-end gap-3">
          <div className="w-40">
            <BrandSelect label="Mes" value={String(mes)} onChange={(e) => setMes(Number(e.target.value))}>
              {MESES.map((m, i) => (
                <option key={m} value={String(i + 1)}>
                  {m}
                </option>
              ))}
            </BrandSelect>
          </div>
          <div className="w-28">
            <BrandSelect label="Año" value={String(anio)} onChange={(e) => setAnio(Number(e.target.value))}>
              {anios.map((y) => (
                <option key={y} value={String(y)}>
                  {y}
                </option>
              ))}
            </BrandSelect>
          </div>
          {esAdmin && (
            <div className="w-52">
              <BrandSelect label="Sector" value={sectorId} onChange={(e) => setSectorId(e.target.value)}>
                {sectores.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </BrandSelect>
            </div>
          )}
        </div>
      </div>

      {error && (
        <p className="rounded-[8px] border border-destructive/20 bg-destructive/10 px-4 py-2.5 font-body text-sm text-foreground">
          {error}
        </p>
      )}

      {filas === null && !error && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 4 }, (_, i) => (
            <BrandSkeleton key={i} className="h-11 w-full" />
          ))}
        </div>
      )}

      {filas !== null && filas.length === 0 && (
        <BrandEmptyState
          icon={BarChart3}
          title="Sin datos para el período"
          description="No hay empleados activos en el sector o no hay bajas registradas."
        />
      )}

      {filas !== null && filas.length > 0 && (
        <div className="overflow-x-auto rounded-[12px] border border-border">
          <table className="w-full min-w-[640px] font-body text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30 text-left font-heading text-[11px] uppercase tracking-[.06em] text-muted-foreground">
                <th className="px-4 py-3">Técnico</th>
                <th className="px-4 py-3 text-right">Días desc.</th>
                <th className="px-4 py-3 text-right">Días enf.</th>
                <th className="px-4 py-3 text-right">Guardias</th>
                <th className="px-4 py-3">Detalle</th>
              </tr>
            </thead>
            <tbody>
              {filas.map((r) => (
                <tr key={r.empleadoId} className="border-b border-border/60 last:border-0">
                  <td className="px-4 py-3">
                    <span className="flex items-center gap-2.5">
                      <span className="flex h-[26px] w-[26px] flex-none items-center justify-center rounded-[6px] bg-brand-orange/80 font-heading text-[9.5px] font-bold text-white">
                        {iniciales(`${r.firstName} ${r.lastName}`)}
                      </span>
                      <span>
                        <span className="block font-semibold text-foreground">
                          {r.lastName}, {r.firstName}
                        </span>
                        <span className="block text-xs text-muted-foreground">
                          {r.cargoNombre}
                        </span>
                      </span>
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-heading text-sm font-bold text-[#ef4444]">
                    {r.diasDescontados}
                  </td>
                  <td className="px-4 py-3 text-right font-heading text-sm font-bold text-[#f59e0b]">
                    {r.diasEnfermedad}
                  </td>
                  <td className="px-4 py-3 text-right font-heading text-sm font-bold text-[#475569] dark:text-[#94a3b8]">
                    {r.guardias}
                  </td>
                  <td className="px-4 py-3 text-[12.5px] text-muted-foreground">
                    {detalle(r)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
