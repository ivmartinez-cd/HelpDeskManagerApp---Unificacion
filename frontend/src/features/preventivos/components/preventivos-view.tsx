"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw, SearchX, Wrench } from "lucide-react";
import { preventivosApi } from "../api/preventivos-api";
import type {
  EquipoPreventivo,
  EstadoPreventivo,
  ZonaParque,
} from "../types/preventivos";
import { PreventivosTabla } from "./preventivos-tabla";
import { useSession } from "@/services/session-provider";
import {
  BrandButton,
  BrandEmptyState,
  BrandInput,
  BrandSkeleton,
} from "@/shared/components/ui/brand-form";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { Switch } from "@/shared/components/ui/switch";
import { cn } from "@/shared/utils/cn";

const POR_PAGINA = 50;

const FILTROS_ESTADO = [
  { value: "", label: "Todos" },
  { value: "vencido", label: "Vencidos" },
  { value: "por_vencer", label: "Por vencer" },
  { value: "al_dia", label: "Al día" },
  { value: "sin_preventivo", label: "Sin preventivo" },
  { value: "sin_frecuencia", label: "Sin frecuencia" },
];

const numberFormat = new Intl.NumberFormat("es-AR");

function formatConsultadoEn(iso: string): string {
  return new Date(iso).toLocaleString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function ZonaChips({
  zonas,
  seleccionada,
  onSelect,
}: {
  zonas: ZonaParque[];
  seleccionada: string | null;
  onSelect: (zona: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2" role="tablist" aria-label="Zona de distribución">
      {zonas.map((z) => {
        const activa = z.zona === seleccionada;
        return (
          <button
            key={z.zona}
            type="button"
            role="tab"
            aria-selected={activa}
            onClick={() => onSelect(z.zona)}
            className={cn(
              "rounded-full border px-3.5 py-1.5 font-body text-xs font-bold transition-colors",
              activa
                ? "border-brand-orange bg-brand-orange/10 text-brand-orange"
                : "border-border bg-card text-muted-foreground hover:text-foreground",
            )}
          >
            {z.zona}
            <span className={cn("ml-1.5 font-semibold tabular-nums", !activa && "opacity-60")}>
              {numberFormat.format(z.maquinas_activas)}
            </span>
          </button>
        );
      })}
    </div>
  );
}

export function PreventivosView() {
  const { user, modules, can } = useSession();
  const tieneModulo = modules.some((m) => m.key === "preventivos");
  const canUpdate = user.isSuperadmin || can("preventivos", "update");

  const [zonas, setZonas] = useState<ZonaParque[] | null>(null);
  const [zona, setZona] = useState<string | null>(null);
  const [rows, setRows] = useState<EquipoPreventivo[] | null>(null);
  const [total, setTotal] = useState(0);
  const [consultadoEn, setConsultadoEn] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [pagina, setPagina] = useState(1);
  const [estado, setEstado] = useState("");
  const [soloHabilitados, setSoloHabilitados] = useState(false);
  const [busqueda, setBusqueda] = useState("");
  const [busquedaAplicada, setBusquedaAplicada] = useState("");

  // La búsqueda espera 350ms de inactividad antes de pegarle al backend.
  useEffect(() => {
    const timer = setTimeout(() => {
      setBusquedaAplicada(busqueda.trim());
      setPagina(1);
    }, 350);
    return () => clearTimeout(timer);
  }, [busqueda]);

  // Catálogo de zonas una sola vez; la primera queda seleccionada.
  useEffect(() => {
    if (!tieneModulo) return;
    preventivosApi
      .listZonas()
      .then((lista) => {
        setZonas(lista);
        setZona((actual) => actual ?? lista[0]?.zona ?? null);
      })
      .catch((err: unknown) => {
        console.error("Error al cargar zonas de preventivos:", err);
        setError("No se pudo consultar el catálogo de zonas en Siges. Reintentá.");
      });
  }, [tieneModulo]);

  const load = useCallback(
    (refresh = false) => {
      if (!zona) return Promise.resolve();
      return preventivosApi
        .listEquipos({
          zona,
          estado: (estado || undefined) as EstadoPreventivo | undefined,
          habilitado: soloHabilitados ? true : undefined,
          q: busquedaAplicada || undefined,
          page: pagina,
          size: POR_PAGINA,
          refresh,
        })
        .then((page) => {
          setRows(page.items);
          setTotal(page.total);
          setConsultadoEn(page.consultado_en);
          setError(null);
        })
        .catch((err: unknown) => {
          console.error("Error al cargar preventivos:", err);
          setError("No se pudo consultar el parque en Siges. Reintentá.");
        });
    },
    [zona, estado, soloHabilitados, busquedaAplicada, pagina],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const handleRefresh = () => {
    setRefreshing(true);
    void load(true).finally(() => setRefreshing(false));
  };

  /** Toggle optimista con rollback: el backend valida permiso igual. */
  const handleToggleHabilitacion = (equipo: EquipoPreventivo) => {
    if (!canUpdate || pendingId !== null || rows === null) return;
    const previos = rows;
    const optimista = equipo.habilitacion
      ? null
      : {
          habilitado_por: user.fullName,
          habilitado_en: new Date().toISOString(),
          nota: null,
        };
    setPendingId(equipo.id_maquina);
    setRows(
      previos.map((r) =>
        r.id_maquina === equipo.id_maquina ? { ...r, habilitacion: optimista } : r,
      ),
    );
    const operacion = equipo.habilitacion
      ? preventivosApi.deshabilitar(equipo.id_maquina).then(() => null)
      : preventivosApi.habilitar(equipo.id_maquina);
    operacion
      .then((habilitacion) => {
        setRows((actuales) =>
          actuales?.map((r) =>
            r.id_maquina === equipo.id_maquina ? { ...r, habilitacion } : r,
          ) ?? actuales,
        );
      })
      .catch((err: unknown) => {
        console.error("Error al cambiar habilitación:", err);
        setRows(previos);
        setError("No se pudo guardar la habilitación. Reintentá.");
      })
      .finally(() => setPendingId(null));
  };

  if (!tieneModulo) {
    return (
      <div className="px-9 py-8">
        <BrandEmptyState
          icon={Wrench}
          title="Sin acceso"
          description="No tenés habilitado el módulo de Preventivos. Pedile acceso a un administrador."
        />
      </div>
    );
  }

  const totalPaginas = Math.max(1, Math.ceil(total / POR_PAGINA));
  const paginaActual = Math.min(pagina, totalPaginas);

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
            Preventivos por zona
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Parque local con su último preventivo y vencimiento · Fuente: Siges (solo lectura)
            · Habilitar = marca interna para despachar al técnico, no toca Gestión.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {consultadoEn && (
            <span className="font-body text-xs text-muted-foreground">
              Datos de las {formatConsultadoEn(consultadoEn)}
            </span>
          )}
          <BrandButton variant="outline" loading={refreshing} onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4" />
            Actualizar
          </BrandButton>
        </div>
      </div>

      {zonas === null && !error && (
        <div className="flex flex-wrap gap-2">
          {Array.from({ length: 10 }, (_, i) => (
            <BrandSkeleton key={i} className="h-8 w-24 rounded-full" />
          ))}
        </div>
      )}
      {zonas !== null && (
        <ZonaChips
          zonas={zonas}
          seleccionada={zona}
          onSelect={(z) => {
            setZona(z);
            setPagina(1);
          }}
        />
      )}

      <div className="flex flex-wrap items-center gap-4">
        <SegmentedControl
          label="Estado"
          size="sm"
          options={FILTROS_ESTADO}
          value={estado}
          onChange={(v) => {
            setEstado(v);
            setPagina(1);
          }}
        />
        <label className="flex items-center gap-2 font-body text-xs font-semibold text-muted-foreground">
          <Switch
            checked={soloHabilitados}
            label="Solo habilitados"
            onCheckedChange={(v) => {
              setSoloHabilitados(v);
              setPagina(1);
            }}
          />
          Solo habilitados
        </label>
        <div className="min-w-[260px]">
          <BrandInput
            label="Buscar"
            type="search"
            placeholder="Cliente, sucursal, serie o modelo…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
        </div>
      </div>

      {rows === null && !error && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 8 }, (_, i) => (
            <BrandSkeleton key={i} className="h-12 w-full" />
          ))}
        </div>
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
              description="Ningún equipo de la zona cumple el filtro actual. Probá cambiar el estado o limpiar la búsqueda."
            />
          ) : (
            <PreventivosTabla
              rows={rows}
              canUpdate={canUpdate}
              pendingId={pendingId}
              onToggleHabilitacion={handleToggleHabilitacion}
            />
          )}

          <div className="flex items-center justify-between gap-3 font-body text-xs text-muted-foreground">
            <span>{numberFormat.format(total)} equipos con el filtro actual</span>
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
            Vencimiento = último preventivo cerrado en Gestión + la frecuencia de la sucursal
            (TipoPreventivo de Siges). &quot;Sin preventivo&quot; / &quot;sin frecuencia&quot;
            se muestran explícitos, sin inventar fechas. La habilitación se limpia sola cuando
            aparece un preventivo posterior. Datos cacheados 5 minutos; &quot;Actualizar&quot;
            fuerza una consulta nueva.
          </p>
        </>
      )}
    </div>
  );
}
