"use client";

import { useCallback, useEffect, useState } from "react";
import { Printer, RefreshCw, SearchX } from "lucide-react";
import { contadoresApi } from "../api/contadores-api";
import type {
  AnexoPendiente,
  AnexosPendientesResumen,
  EstadoAnexoPendiente,
} from "../types/anexos-pendientes";
import { AnexosPendientesPrintSheet } from "./anexos-pendientes-print-sheet";
import { AnexosPendientesTabla, formatPeriodo } from "./anexos-pendientes-tabla";
import {
  BrandButton,
  BrandEmptyState,
  BrandInput,
  BrandSkeleton,
} from "@/shared/components/ui/brand-form";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { SigesLoadingModal } from "@/shared/components/ui/siges-loading-modal";

const FILTROS_ESTADO = [
  { value: "todos", label: "Todos" },
  { value: "en_proceso", label: "En proceso" },
  { value: "demorado", label: "Demorados" },
];

const usdFormat = new Intl.NumberFormat("es-AR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

function KpiCard({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className="flex min-w-[120px] flex-col gap-0.5 rounded-[12px] border border-border bg-card px-4 py-3">
      <span className={`font-heading text-2xl font-extrabold tabular-nums ${tone}`}>
        {value}
      </span>
      <span className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
    </div>
  );
}

function formatConsultadoEn(iso: string): string {
  return new Date(iso).toLocaleString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function AnexosPendientesView() {
  const [rows, setRows] = useState<AnexoPendiente[] | null>(null);
  const [resumen, setResumen] = useState<AnexosPendientesResumen | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [estado, setEstado] = useState("todos");
  const [busqueda, setBusqueda] = useState("");
  const [busquedaAplicada, setBusquedaAplicada] = useState("");

  // La búsqueda espera 350ms de inactividad antes de pegarle al backend.
  useEffect(() => {
    const timer = setTimeout(() => setBusquedaAplicada(busqueda.trim()), 350);
    return () => clearTimeout(timer);
  }, [busqueda]);

  const load = useCallback(
    (refresh = false) => {
      const lista = contadoresApi
        .listAnexosPendientes({
          estado: estado === "todos" ? undefined : (estado as EstadoAnexoPendiente),
          search: busquedaAplicada || undefined,
          refresh,
        })
        .then((items) => {
          setRows(items);
          setError(null);
        });
      const kpis = contadoresApi.getAnexosPendientesResumen().then(setResumen);
      return Promise.all([lista, kpis]).catch((err: unknown) => {
        console.error("Error al cargar anexos sin facturar:", err);
        setError("No se pudo consultar. Reintentá en unos segundos.");
      });
    },
    [estado, busquedaAplicada],
  );

  const handleRefresh = () => {
    setRefreshing(true);
    void load(true).finally(() => setRefreshing(false));
  };

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
            Anexos sin facturar
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Cierre de contadores: anexos de Impresión con el período abierto · Solo lectura
            {resumen && <> · Período en proceso: {formatPeriodo(resumen.periodo_referencia)}</>}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {resumen && (
            <span className="font-body text-xs text-muted-foreground">
              Datos de las {formatConsultadoEn(resumen.consultado_en)}
            </span>
          )}
          <BrandButton variant="outline" loading={refreshing} onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4" />
            Actualizar
          </BrandButton>
          <BrandButton onClick={() => window.print()} disabled={!rows || rows.length === 0}>
            <Printer className="h-4 w-4" />
            Imprimir
          </BrandButton>
        </div>
      </div>

      {resumen && (
        <div className="flex flex-wrap gap-3">
          <KpiCard
            label="Pendientes"
            value={String(resumen.total)}
            tone="text-foreground"
          />
          <KpiCard
            label={`En proceso · ${formatPeriodo(resumen.periodo_referencia)}`}
            value={String(resumen.en_proceso)}
            tone="text-warning"
          />
          <KpiCard
            label="Demorados"
            value={String(resumen.demorados)}
            tone="text-destructive"
          />
          <KpiCard
            label="USD pendiente"
            value={usdFormat.format(Number(resumen.importe_usd_total))}
            tone="text-brand-orange"
          />
        </div>
      )}

      <div className="flex flex-wrap items-end gap-3">
        <SegmentedControl
          label="Estado"
          size="sm"
          options={FILTROS_ESTADO}
          value={estado}
          onChange={setEstado}
        />
        <div className="min-w-[260px]">
          <BrandInput
            label="Buscar"
            type="search"
            placeholder="Grupo, contrato, anexo, vendedor o período…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
        </div>
      </div>

      {rows === null && !error && (
        <>
          <SigesLoadingModal
            etapas={[
              { hasta: 5, texto: "Consultando los anexos con período abierto…" },
              { hasta: 12, texto: "Cruzando los procesos de facturación…" },
              { hasta: 20, texto: "Un momento más, ya casi está…" },
              { texto: "La base está lenta hoy — seguimos esperando la respuesta…" },
            ]}
            nota="La primera carga cruza los procesos de facturación. Después queda en caché 5 minutos y la página responde al instante."
          />
          <div className="flex flex-col gap-2">
            {Array.from({ length: 8 }, (_, i) => (
              <BrandSkeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </>
      )}

      {error && (
        <div className="flex items-center justify-between gap-4 rounded-[12px] border border-destructive/20 bg-destructive/10 px-5 py-4">
          <p className="font-body text-sm text-foreground">{error}</p>
          <BrandButton variant="outline" size="sm" onClick={() => void load()}>
            Reintentar
          </BrandButton>
        </div>
      )}

      {rows !== null && !error && (
        <>
          {rows.length === 0 ? (
            <BrandEmptyState
              icon={SearchX}
              title="Sin anexos pendientes"
              description="Ningún anexo cumple el filtro actual. Si no hay filtros activos, el cierre está al día."
            />
          ) : (
            <AnexosPendientesTabla rows={rows} />
          )}

          <p className="font-body text-xs text-muted-foreground">
            {rows.length} anexos con el filtro actual
          </p>

          <p className="rounded-[8px] bg-muted/30 px-4 py-3 font-body text-xs text-muted-foreground">
            Reemplaza el reporte &quot;Anexos No Facturados&quot; de sitesphp acotado al cierre
            de contadores: solo anexos de Impresión, mes en curso afuera y sin lo ya
            facturado/liberado/a liberar. EN PROCESO = período del mes anterior; DEMORADO =
            períodos más viejos. Los datos se cachean 5 minutos; &quot;Actualizar&quot; fuerza
            una consulta nueva. &quot;Imprimir&quot; saca el reporte con el filtro aplicado.
          </p>

          <AnexosPendientesPrintSheet rows={rows} resumen={resumen} />
        </>
      )}
    </div>
  );
}
