"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { CalendarOff, Plus } from "lucide-react";
import type {
  AlcanceOption,
  Cobertura,
  CoberturaEntityType,
  CoberturaEstadoUi,
  CoberturaOperadorOption,
  FilaCoberturas,
  Intercambio,
} from "../types/coberturas";
import { COBERTURA_CONFIG } from "../lib/config";
import { agruparFilas, estadoFila, filaCoincide } from "../lib/intercambios";
import { CancelarCoberturaModal } from "./cancelar-cobertura-modal";
import { CoberturaModal } from "./cobertura-modal";
import { CoberturasTabla } from "./coberturas-tabla";
import { useSession } from "@/services/session-provider";
import {
  BrandButton,
  BrandEmptyState,
  BrandInput,
  BrandSkeleton,
} from "@/shared/components/ui/brand-form";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";

const FILTROS: { value: "todos" | CoberturaEstadoUi; label: string }[] = [
  { value: "todos", label: "Todas" },
  { value: "activa", label: "Activa" },
  { value: "programada", label: "Programada" },
  { value: "vencida", label: "Vencida" },
  { value: "cancelada", label: "Cancelada" },
];

const POR_PAGINA = 20;

export function CoberturasView({ entityType }: { entityType: CoberturaEntityType }) {
  const config = COBERTURA_CONFIG[entityType];
  const { user, can } = useSession();
  const puedeCrear =
    user.isSuperadmin || can(config.permisoCrear.moduleKey, config.permisoCrear.actionKey);
  const puedeMutar =
    user.isSuperadmin || can(config.permisoMutar.moduleKey, config.permisoMutar.actionKey);

  const [coberturas, setCoberturas] = useState<Cobertura[] | null>(null);
  const [operadores, setOperadores] = useState<CoberturaOperadorOption[]>([]);
  const [alcanceOptions, setAlcanceOptions] = useState<AlcanceOption[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [filtroEstado, setFiltroEstado] = useState<"todos" | CoberturaEstadoUi>("todos");
  const [busqueda, setBusqueda] = useState("");
  const [pagina, setPagina] = useState(1);
  const [creando, setCreando] = useState(false);
  const [editando, setEditando] = useState<Cobertura | null>(null);
  const [editandoIntercambio, setEditandoIntercambio] = useState<Intercambio | null>(null);
  const [cancelando, setCancelando] = useState<FilaCoberturas | null>(null);
  const [cancelandoBusy, setCancelandoBusy] = useState(false);

  const load = useCallback(
    () =>
      Promise.all([
        config.api.list(),
        config.api.listOperadores(),
        config.api.listAlcanceOptions(),
      ])
        .then(([items, ops, alcances]) => {
          setCoberturas(items);
          setOperadores(ops);
          setAlcanceOptions(alcances);
          setError(null);
        })
        .catch((err: unknown) => {
          console.error("Error al cargar coberturas:", err);
          setError("No se pudieron cargar las coberturas. Intentá de nuevo.");
        }),
    [config.api],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const operadorMeta = useMemo(
    () => new Map(operadores.map((o) => [o.id, o])),
    [operadores],
  );
  const alcanceLabelMap = useMemo(
    () => new Map(alcanceOptions.map((o) => [o.id, o.label])),
    [alcanceOptions],
  );

  // Un intercambio (ADR-026) son dos filas del listado plano: se agrupan
  // en una sola antes de filtrar y paginar.
  const filtradas = useMemo(() => {
    if (!coberturas) return [];
    const q = busqueda.trim().toLowerCase();
    return agruparFilas(coberturas).filter((fila) => {
      if (filtroEstado !== "todos" && estadoFila(fila) !== filtroEstado) return false;
      return !q || filaCoincide(fila, q);
    });
  }, [coberturas, filtroEstado, busqueda]);

  const totalPaginas = Math.max(1, Math.ceil(filtradas.length / POR_PAGINA));
  const paginaActual = Math.min(pagina, totalPaginas);
  const visibles = filtradas.slice((paginaActual - 1) * POR_PAGINA, paginaActual * POR_PAGINA);

  const handleEditar = (fila: FilaCoberturas) => {
    if (fila.tipo === "cobertura") setEditando(fila.cobertura);
    else setEditandoIntercambio(fila.intercambio);
  };

  const handleCancelar = () => {
    if (!cancelando) return;
    setCancelandoBusy(true);
    const peticion =
      cancelando.tipo === "cobertura"
        ? config.api.cancel(cancelando.cobertura.id)
        : (config.intercambios?.cancel(cancelando.intercambio.id) ??
          Promise.reject(new Error("Este módulo no habilita intercambios.")));
    peticion
      .then(() => {
        setCancelando(null);
        return load();
      })
      .catch((err: unknown) => {
        console.error("Error al cancelar la cobertura:", err);
        setError("No se pudo cancelar la cobertura. Intentá de nuevo.");
        setCancelando(null);
      })
      .finally(() => setCancelandoBusy(false));
  };

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
            Coberturas
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Reemplazos temporales de operadores · {config.subtitulo} · No modifican la fuente
            externa.
          </p>
        </div>
        {puedeCrear && (
          <BrandButton onClick={() => setCreando(true)}>
            <Plus className="h-4 w-4" />
            Nueva cobertura
          </BrandButton>
        )}
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <SegmentedControl
          label="Filtrar por estado"
          size="sm"
          options={FILTROS}
          value={filtroEstado}
          onChange={(v) => {
            setFiltroEstado(v as typeof filtroEstado);
            setPagina(1);
          }}
        />
        <div className="min-w-[220px]">
          <BrandInput
            label="Buscar"
            type="search"
            placeholder="Buscá operador…"
            value={busqueda}
            onChange={(e) => {
              setBusqueda(e.target.value);
              setPagina(1);
            }}
          />
        </div>
        {(filtroEstado !== "todos" || busqueda) && (
          <button
            type="button"
            onClick={() => {
              setFiltroEstado("todos");
              setBusqueda("");
              setPagina(1);
            }}
            className="pb-2.5 font-body text-xs text-muted-foreground hover:text-brand-orange"
          >
            Limpiar filtros
          </button>
        )}
      </div>

      {coberturas === null && !error && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 5 }, (_, i) => (
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

      {coberturas !== null && !error && (
        <>
          {filtradas.length === 0 ? (
            <BrandEmptyState
              icon={CalendarOff}
              title="No hay coberturas todavía"
              description="Creá una cobertura para que otro operador atienda durante una ausencia."
            />
          ) : (
            <CoberturasTabla
              rows={visibles}
              operadorMeta={operadorMeta}
              alcanceLabelOf={(id) => alcanceLabelMap.get(id) ?? id}
              alcanceUnidad={config.alcanceUnidad}
              canEdit={puedeMutar}
              canCancel={puedeMutar}
              onEdit={handleEditar}
              onCancel={setCancelando}
            />
          )}

          {totalPaginas > 1 && (
            <div className="flex items-center justify-end gap-3 font-body text-xs text-muted-foreground">
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

          <p className="rounded-[8px] bg-muted/30 px-4 py-3 font-body text-xs text-muted-foreground">
            {config.footerCopy}
          </p>
        </>
      )}

      {(creando || editando || editandoIntercambio) && (
        <CoberturaModal
          config={config}
          operadores={operadores}
          alcanceOptions={alcanceOptions}
          cobertura={editando}
          intercambio={editandoIntercambio}
          onClose={() => {
            setCreando(false);
            setEditando(null);
            setEditandoIntercambio(null);
          }}
          onSaved={() => {
            setCreando(false);
            setEditando(null);
            setEditandoIntercambio(null);
            void load();
          }}
        />
      )}

      {cancelando && (
        <CancelarCoberturaModal
          fila={cancelando}
          alcanceUnidad={config.alcanceUnidad}
          busy={cancelandoBusy}
          onVolver={() => setCancelando(null)}
          onConfirmar={handleCancelar}
        />
      )}
    </div>
  );
}
