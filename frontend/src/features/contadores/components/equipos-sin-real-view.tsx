"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw, SearchX } from "lucide-react";
import { contadoresApi } from "../api/contadores-api";
import type {
  EquipoSinReal,
  EquiposSinRealResumen,
  EquiposSinRealSortKey,
} from "../types/equipos-sin-real";
import { EquiposSinRealLoadingModal } from "./equipos-sin-real-loading-modal";
import { EquiposSinRealTabla } from "./equipos-sin-real-tabla";
import {
  BrandButton,
  BrandEmptyState,
  BrandInput,
  BrandSkeleton,
} from "@/shared/components/ui/brand-form";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { useTableSort } from "@/shared/hooks/use-table-sort";

const POR_PAGINA = 50;
const SORT_KEYS: readonly EquiposSinRealSortKey[] = [
  "meses",
  "cliente",
  "sucursal",
  "modelo",
  "operador",
];

/** Cortes alineados a los umbrales de severidad del backend
 * (`severidad_sin_real.py`): 3+ medio, 6+ alto, 12+ crítico. */
const FILTROS_MESES = [
  { value: "1", label: "Todos (1+)" },
  { value: "3", label: "3+ meses" },
  { value: "6", label: "6+ meses" },
  { value: "12", label: "12+ meses" },
];

function KpiCard({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className="flex min-w-[120px] flex-col gap-0.5 rounded-[12px] border border-border bg-card px-4 py-3">
      <span className={`font-heading text-2xl font-extrabold tabular-nums ${tone}`}>
        {new Intl.NumberFormat("es-AR").format(value)}
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

export function EquiposSinRealView() {
  const [rows, setRows] = useState<EquipoSinReal[] | null>(null);
  const [total, setTotal] = useState(0);
  const [resumen, setResumen] = useState<EquiposSinRealResumen | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [pagina, setPagina] = useState(1);
  const [minMeses, setMinMeses] = useState("3");
  const [busqueda, setBusqueda] = useState("");
  const [busquedaAplicada, setBusquedaAplicada] = useState("");
  const { sort, toggleSort } = useTableSort<EquiposSinRealSortKey>({
    initial: { key: "meses", direction: "desc" },
    keys: SORT_KEYS,
    descFirstKeys: ["meses"],
  });

  // La búsqueda espera 350ms de inactividad antes de pegarle al backend.
  useEffect(() => {
    const timer = setTimeout(() => {
      setBusquedaAplicada(busqueda.trim());
      setPagina(1);
    }, 350);
    return () => clearTimeout(timer);
  }, [busqueda]);

  const load = useCallback(
    (refresh = false) => {
      const lista = contadoresApi
        .listEquiposSinReal({
          page: pagina,
          size: POR_PAGINA,
          sortBy: sort.key,
          sortDir: sort.direction,
          minMeses: Number(minMeses),
          search: busquedaAplicada || undefined,
          refresh,
        })
        .then((page) => {
          setRows(page.items);
          setTotal(page.total);
          setError(null);
        });
      const kpis = contadoresApi.getEquiposSinRealResumen().then(setResumen);
      return Promise.all([lista, kpis])
        .catch((err: unknown) => {
          console.error("Error al cargar equipos sin contador real:", err);
          setError(
            "No se pudo consultar Siges. La consulta puede tardar (~10s la primera vez); reintentá.",
          );
        });
    },
    [pagina, sort, minMeses, busquedaAplicada],
  );

  const handleRefresh = () => {
    setRefreshing(true);
    void load(true).finally(() => setRefreshing(false));
  };

  useEffect(() => {
    void load();
  }, [load]);

  const totalPaginas = Math.max(1, Math.ceil(total / POR_PAGINA));
  const paginaActual = Math.min(pagina, totalPaginas);

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
            Equipos sin contador real
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Parque que sigue facturando con estimados · Fuente: Siges (solo lectura) · Para el
            laburo mes a mes de recuperación de reales.
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
        </div>
      </div>

      {resumen && (
        <div className="flex flex-wrap gap-3">
          <KpiCard label="Sin real (1+ mes)" value={resumen.total} tone="text-foreground" />
          <KpiCard label="Críticos · 12+" value={resumen.criticos} tone="text-destructive" />
          <KpiCard label="Altos · 6-11" value={resumen.altos} tone="text-brand-orange" />
          <KpiCard label="Medios · 3-5" value={resumen.medios} tone="text-warning" />
          <KpiCard label="Nunca real" value={resumen.nunca_real} tone="text-destructive" />
        </div>
      )}

      <div className="flex flex-wrap items-end gap-3">
        <SegmentedControl
          label="Meses sin real"
          size="sm"
          options={FILTROS_MESES}
          value={minMeses}
          onChange={(v) => {
            setMinMeses(v);
            setPagina(1);
          }}
        />
        <div className="min-w-[260px]">
          <BrandInput
            label="Buscar"
            type="search"
            placeholder="Serie, cliente, sucursal, modelo u operador…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
        </div>
      </div>

      {rows === null && !error && (
        <>
          <EquiposSinRealLoadingModal />
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
              title="Sin resultados"
              description="Ningún equipo cumple el filtro actual. Probá bajar el umbral de meses o limpiar la búsqueda."
            />
          ) : (
            <EquiposSinRealTabla rows={rows} sort={sort} onToggleSort={toggleSort} />
          )}

          <div className="flex items-center justify-between gap-3 font-body text-xs text-muted-foreground">
            <span>
              {new Intl.NumberFormat("es-AR").format(total)} equipos con el filtro actual
            </span>
            {totalPaginas > 1 && (
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  disabled={paginaActual === 1}
                  onClick={() => setPagina(paginaActual - 1)}
                  className="rounded-[6px] px-2 py-1 hover:bg-muted disabled:opacity-40"
                >
                  ← Anterior
                </button>
                <span>
                  Página {paginaActual} de {totalPaginas}
                </span>
                <button
                  type="button"
                  disabled={paginaActual === totalPaginas}
                  onClick={() => setPagina(paginaActual + 1)}
                  className="rounded-[6px] px-2 py-1 hover:bg-muted disabled:opacity-40"
                >
                  Siguiente →
                </button>
              </div>
            )}
          </div>

          <p className="rounded-[8px] bg-muted/30 px-4 py-3 font-body text-xs text-muted-foreground">
            &quot;Sin real&quot; = sin ninguna toma de contador real (teléfono, mail, automático,
            informe de servicio técnico, etc.) — solo estimados. Reemplaza el reporte
            &quot;Equipos Sin Contadores Reales&quot; de sitesphp; los datos se cachean 10
            minutos, &quot;Actualizar&quot; fuerza una consulta nueva.
          </p>
        </>
      )}
    </div>
  );
}
