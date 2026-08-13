"use client";

import { Fragment, useCallback, useEffect, useState } from "react";
import { ChevronRight, ScrollText, Search } from "lucide-react";
import { BrandButton, BrandEmptyState, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { configApi } from "../api/config-api";
import {
  ACCION_LABEL,
  descripcionRegistro,
  detalleRegistro,
  ENTIDAD_LABEL,
} from "../lib/auditoria";
import { ReportesAuditoriaTabs } from "./reportes-auditoria-tabs";
import type { Page, RegistroAuditoria } from "../types/vacaciones";

const PAGE_SIZE = 50;

function formatFechaHora(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }) + " " + d.toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" });
}

export function AuditoriaView() {
  const [busqueda, setBusqueda] = useState("");
  const [pagina, setPagina] = useState(1);
  const [data, setData] = useState<Page<RegistroAuditoria> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandido, setExpandido] = useState<string | null>(null);

  const load = useCallback((search: string, page: number) => {
    configApi
      .listAuditoria({ search: search || undefined, page, size: PAGE_SIZE })
      .then((p) => {
        setData(p);
        setError(null);
      })
      .catch((err: unknown) => {
        console.error("Error al cargar la auditoría:", err);
        setError("No se pudo cargar el registro de auditoría.");
      });
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => load(busqueda, pagina), busqueda ? 350 : 0);
    return () => clearTimeout(timer);
  }, [busqueda, pagina, load]);

  const registros = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPaginas = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-col gap-1.5">
        <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
          Auditoría
        </h1>
        <p className="font-body text-sm text-muted-foreground">
          Registro de cambios del módulo · Solo admin
        </p>
      </div>

      <ReportesAuditoriaTabs />

      <div className="relative">
        <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          placeholder="Buscar por acción, entidad o usuario…"
          value={busqueda}
          onChange={(e) => {
            setBusqueda(e.target.value);
            setPagina(1);
          }}
          className="w-full rounded-[9px] border border-border bg-card py-2.5 pl-11 pr-4 font-body text-[13.5px] text-foreground outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-brand-orange/40"
        />
      </div>

      {error && (
        <div className="flex items-center justify-between gap-4 rounded-[12px] border border-destructive/20 bg-destructive/10 px-5 py-4">
          <p className="font-body text-sm text-foreground">{error}</p>
          <BrandButton variant="outline" size="sm" onClick={() => load(busqueda, pagina)}>
            Reintentar
          </BrandButton>
        </div>
      )}

      {data === null && !error && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 6 }, (_, i) => (
            <BrandSkeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      )}

      {data !== null && registros.length === 0 && !error && (
        <BrandEmptyState
          icon={ScrollText}
          title="Sin registros de auditoría"
          description="Los cambios del módulo van a aparecer acá a medida que sucedan."
        />
      )}

      {registros.length > 0 && (
        <>
          <div className="overflow-x-auto rounded-[12px] border border-border">
            <table className="w-full min-w-[760px] font-body text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/30 text-left font-heading text-[10.5px] uppercase tracking-[.05em] text-muted-foreground">
                  <th className="px-4 py-3">Fecha</th>
                  <th className="px-4 py-3">Acción</th>
                  <th className="px-4 py-3">Entidad</th>
                  <th className="px-4 py-3">Descripción</th>
                  <th className="px-4 py-3">Usuario</th>
                  <th className="w-9 px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {registros.map((r) => {
                  const accion = ACCION_LABEL[r.accion] ?? {
                    label: r.accion,
                    bg: "rgba(100,116,139,.14)",
                    color: "#94a3b8",
                  };
                  const abierto = expandido === r.id;
                  return (
                    <Fragment key={r.id}>
                      <tr className="border-b border-border/60 last:border-0">
                        <td className="whitespace-nowrap px-4 py-3 text-[12.5px] text-muted-foreground">
                          {formatFechaHora(r.createdAt)}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className="inline-block rounded-[20px] px-2.5 py-0.5 text-[11.5px] font-semibold"
                            style={{ backgroundColor: accion.bg, color: accion.color }}
                          >
                            {accion.label}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-semibold text-foreground">
                          {ENTIDAD_LABEL[r.entidad] ?? r.entidad}
                        </td>
                        <td className="max-w-[280px] truncate px-4 py-3 text-muted-foreground">
                          {descripcionRegistro(r)}
                        </td>
                        <td className="px-4 py-3 text-foreground">
                          {r.usuarioEmail ?? "—"}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <button
                            type="button"
                            onClick={() => setExpandido(abierto ? null : r.id)}
                            aria-label={abierto ? "Colapsar" : "Expandir"}
                            className="text-muted-foreground hover:text-foreground"
                          >
                            <ChevronRight
                              className={`h-4 w-4 transition-transform ${abierto ? "rotate-90" : ""}`}
                            />
                          </button>
                        </td>
                      </tr>
                      {abierto && (
                        <tr className="border-b border-border/60 bg-muted/20 last:border-0">
                          <td colSpan={6} className="px-4 py-3 pl-11">
                            <dl className="grid max-w-[600px] grid-cols-[auto_1fr] gap-x-4 gap-y-1">
                              {detalleRegistro(r).map(({ clave, valor }) => (
                                <Fragment key={clave}>
                                  <dt className="font-body text-[12.5px] font-semibold text-muted-foreground">
                                    {clave}
                                  </dt>
                                  <dd className="font-body text-[12.5px] text-foreground">
                                    {valor}
                                  </dd>
                                </Fragment>
                              ))}
                              {r.entidadId && (
                                <Fragment>
                                  <dt className="font-body text-[12.5px] font-semibold text-muted-foreground">
                                    ID
                                  </dt>
                                  <dd className="font-mono text-[11.5px] text-muted-foreground">
                                    {r.entidadId}
                                  </dd>
                                </Fragment>
                              )}
                            </dl>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between">
            <p className="font-body text-[12.5px] text-muted-foreground">
              Mostrando {registros.length} de {total} registros
            </p>
            {totalPaginas > 1 && (
              <div className="flex items-center gap-2">
                <BrandButton
                  variant="outline"
                  size="sm"
                  disabled={pagina <= 1}
                  onClick={() => setPagina((p) => p - 1)}
                >
                  Anterior
                </BrandButton>
                <span className="font-body text-xs text-muted-foreground">
                  {pagina} / {totalPaginas}
                </span>
                <BrandButton
                  variant="outline"
                  size="sm"
                  disabled={pagina >= totalPaginas}
                  onClick={() => setPagina((p) => p + 1)}
                >
                  Siguiente
                </BrandButton>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
