"use client";

import { RefreshCw, SearchX, Wrench } from "lucide-react";
import { POR_PAGINA, usePreventivosView } from "../hooks/use-preventivos-view";
import { usePuntosMapa } from "../hooks/use-puntos-mapa";
import { formatConsultadoEn, numberFormat } from "./preventivos-format";
import { PreventivosMapa } from "./preventivos-mapa";
import { PreventivosMapaLeyenda } from "./preventivos-mapa-leyenda";
import { PreventivosTabla } from "./preventivos-tabla";
import { ZonaChips } from "./zona-chips";
import {
  BrandButton,
  BrandEmptyState,
  BrandInput,
  BrandSkeleton,
} from "@/shared/components/ui/brand-form";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { SigesLoadingModal } from "@/shared/components/ui/siges-loading-modal";
import { Switch } from "@/shared/components/ui/switch";

const FILTROS_ESTADO = [
  { value: "", label: "Todos" },
  { value: "vencido", label: "Vencidos" },
  { value: "por_vencer", label: "Por vencer" },
  { value: "al_dia", label: "Al día" },
  { value: "sin_preventivo", label: "Sin preventivo" },
  { value: "sin_frecuencia", label: "Sin frecuencia" },
];

const FILTROS_VISTA = [
  { value: "tabla", label: "Tabla" },
  { value: "mapa", label: "Mapa" },
];

export function PreventivosView() {
  const {
    tieneModulo,
    canUpdate,
    zonas,
    zona,
    rows,
    total,
    consultadoEn,
    error,
    refreshing,
    pendingId,
    pagina,
    estado,
    soloHabilitados,
    busqueda,
    busquedaAplicada,
    vista,
    setVista,
    setBusqueda,
    setPagina,
    load,
    handleRefresh,
    handleToggleHabilitacion,
    handleSelectZona,
    handleEstadoChange,
    handleSoloHabilitadosChange,
  } = usePreventivosView();

  const mapa = usePuntosMapa({
    activo: vista === "mapa",
    zona,
    estado,
    soloHabilitados,
    busquedaAplicada,
  });

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
            Parque local con su último preventivo y vencimiento · Solo lectura
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
        <ZonaChips zonas={zonas} seleccionada={zona} onSelect={handleSelectZona} />
      )}

      <div className="flex flex-wrap items-center gap-4">
        <SegmentedControl
          label="Vista"
          size="sm"
          options={FILTROS_VISTA}
          value={vista}
          onChange={(v) => setVista(v as "tabla" | "mapa")}
        />
        <SegmentedControl
          label="Estado"
          size="sm"
          options={FILTROS_ESTADO}
          value={estado}
          onChange={handleEstadoChange}
        />
        <label className="flex items-center gap-2 font-body text-xs font-semibold text-muted-foreground">
          <Switch
            checked={soloHabilitados}
            label="Solo habilitados"
            onCheckedChange={handleSoloHabilitadosChange}
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

      {vista === "tabla" && rows === null && !error && (
        <>
          {zona !== null && (
            <SigesLoadingModal
              etapas={[
                { hasta: 4, texto: `Consultando el parque de la zona ${zona}…` },
                { hasta: 12, texto: "Calculando últimos preventivos y vencimientos…" },
                { hasta: 20, texto: "Un momento más, ya casi está…" },
                { texto: "La base está lenta hoy — seguimos esperando la respuesta…" },
              ]}
              nota="La primera carga de cada zona cruza el historial de incidentes y contadores (~5-10 segundos). Después queda en caché 5 minutos y responde al instante."
            />
          )}
          <div className="flex flex-col gap-2">
            {Array.from({ length: 8 }, (_, i) => (
              <BrandSkeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </>
      )}

      {vista === "tabla" && error && (
        <div className="flex items-center justify-between gap-4 rounded-[12px] border border-destructive/20 bg-destructive/10 px-5 py-4">
          <p className="font-body text-sm text-foreground">{error}</p>
          <BrandButton variant="outline" size="sm" onClick={() => void load()}>
            Reintentar
          </BrandButton>
        </div>
      )}

      {vista === "tabla" && rows !== null && !error && (
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
            (TipoPreventivo). &quot;Sin preventivo&quot; / &quot;sin frecuencia&quot;
            se muestran explícitos, sin inventar fechas. La habilitación se limpia sola cuando
            aparece un preventivo posterior. Datos cacheados 5 minutos; &quot;Actualizar&quot;
            fuerza una consulta nueva.
          </p>
        </>
      )}

      {vista === "mapa" && (
        <>
          {mapa.error && (
            <div className="flex items-center justify-between gap-4 rounded-[12px] border border-destructive/20 bg-destructive/10 px-5 py-4">
              <p className="font-body text-sm text-foreground">{mapa.error}</p>
            </div>
          )}
          {!mapa.error && mapa.puntos === null && (
            <BrandSkeleton className="h-[520px] w-full rounded-[12px]" />
          )}
          {!mapa.error && mapa.puntos !== null && (
            <>
              {mapa.puntos.length === 0 ? (
                <BrandEmptyState
                  icon={SearchX}
                  title="Sin resultados"
                  description="Ningún equipo de la zona cumple el filtro actual. Probá cambiar el estado o limpiar la búsqueda."
                />
              ) : (
                <>
                  {mapa.sinUbicar > 0 && (
                    <div className="flex flex-wrap items-center justify-between gap-3 rounded-[8px] bg-muted/30 px-4 py-3">
                      <p className="font-body text-xs text-muted-foreground">
                        {numberFormat.format(mapa.sinUbicar)} sucursal(es) del filtro actual no
                        tienen una coordenada válida en Siges y no se muestran en el mapa.
                      </p>
                      {canUpdate && (
                        <BrandButton
                          variant="outline"
                          size="sm"
                          loading={mapa.geocodificando}
                          onClick={mapa.geocodificar}
                          title="Geocodifica el universo completo de sucursales sin ubicar, no solo la zona actual"
                        >
                          Geocodificar sucursales sin ubicar
                        </BrandButton>
                      )}
                    </div>
                  )}
                  <PreventivosMapa puntos={mapa.puntos} />
                  <PreventivosMapaLeyenda />
                </>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
