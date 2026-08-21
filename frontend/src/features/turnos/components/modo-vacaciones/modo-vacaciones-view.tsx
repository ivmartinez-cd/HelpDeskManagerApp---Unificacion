"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { CalendarOff, Plus } from "lucide-react";
import { grillaVariantesApi } from "../../api/grilla-variantes-api";
import { turnosApi } from "../../api/turnos-api";
import type { Casilla, Slot, UserOption } from "../../types/turnos";
import type { GrillaVariante, VarianteEstadoUi } from "../../types/grilla-variantes";
import { deriveEstadoVariante, formatFecha } from "../../lib/variante-estado";
import { VarianteEditor, type PrecargaInicial } from "./variante-editor";
import { VariantePreviewModal } from "./variante-preview-modal";
import { VariantesTabla } from "./variantes-tabla";
import { BrandButton, BrandEmptyState, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { useSession } from "@/services/session-provider";

const FILTROS: { value: "todas" | VarianteEstadoUi; label: string }[] = [
  { value: "todas", label: "Todas" },
  { value: "vigente", label: "Vigente" },
  { value: "programada", label: "Programada" },
  { value: "vencida", label: "Vencida" },
  { value: "cancelada", label: "Cancelada" },
];

interface ModoVacacionesViewProps {
  /** Llegada desde Aprobaciones (query params): abre el editor precargado. */
  precargaInicial?: PrecargaInicial | null;
}

/** Sección "Modo vacaciones" de /turnos (ADR-025): listado de grillas
 * de vacaciones (vigente + programadas + historial) con cancelar/editar, y el
 * editor de variante. Modales/editor por estado local, no por ruta. */
export function ModoVacacionesView({ precargaInicial = null }: ModoVacacionesViewProps) {
  // Crear/editar/cancelar grillas es turnos.manage (ADR-029); con view solo se
  // listan y previsualizan.
  const { can } = useSession();
  const puedeEditar = can("turnos", "manage");
  const [variantes, setVariantes] = useState<GrillaVariante[] | null>(null);
  const [casillas, setCasillas] = useState<Casilla[]>([]);
  const [titular, setTitular] = useState<Slot[]>([]);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [filtro, setFiltro] = useState<"todas" | VarianteEstadoUi>("todas");
  const [editor, setEditor] = useState<
    | { modo: "cerrado" }
    | { modo: "alta"; precarga: PrecargaInicial | null }
    | { modo: "edicion"; variante: GrillaVariante }
  >(() => (precargaInicial ? { modo: "alta", precarga: precargaInicial } : { modo: "cerrado" }));
  const [cancelando, setCancelando] = useState<GrillaVariante | null>(null);
  const [previsualizando, setPrevisualizando] = useState<GrillaVariante | null>(null);
  const [cancelandoBusy, setCancelandoBusy] = useState(false);
  const [ultimaGuardada, setUltimaGuardada] = useState<GrillaVariante | null>(null);

  const load = useCallback(
    () =>
      Promise.all([
        grillaVariantesApi.list(),
        turnosApi.listCasillas(),
        turnosApi.listSlots(),
        turnosApi.listAssignableUsers(),
      ])
        .then(([vs, cs, ss, us]) => {
          setVariantes(vs);
          setCasillas(cs.filter((c) => c.isActive));
          setTitular(ss);
          setUsers(us);
          setError(null);
        })
        .catch((err: unknown) => {
          console.error("Error al cargar el modo vacaciones:", err);
          setError("No se pudo cargar el modo vacaciones. Intentá de nuevo.");
        }),
    [],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const filtradas = useMemo(
    () => (variantes ?? []).filter((v) => filtro === "todas" || deriveEstadoVariante(v) === filtro),
    [variantes, filtro],
  );

  const handleCancelar = () => {
    if (!cancelando) return;
    setCancelandoBusy(true);
    grillaVariantesApi
      .cancel(cancelando.id)
      .then(() => {
        setCancelando(null);
        return load();
      })
      .catch((err: unknown) => {
        console.error("Error al cancelar la grilla de vacaciones:", err);
        setError("No se pudo cancelar la grilla. Intentá de nuevo.");
        setCancelando(null);
      })
      .finally(() => setCancelandoBusy(false));
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <p className="max-w-2xl font-body text-sm text-muted-foreground">
          Grilla alternativa de franjas y operadores para un rango de fechas (vacaciones, licencias).
          Se aplica en lectura sobre Turnos del día y, al vencer, la grilla titular vuelve sola — sin
          acción ni job. Para reemplazar solo a una persona sin cambiar horarios, usá Coberturas.
        </p>
        {puedeEditar && editor.modo === "cerrado" && (
          <BrandButton onClick={() => setEditor({ modo: "alta", precarga: null })}>
            <Plus className="h-4 w-4" />
            Nueva grilla de vacaciones
          </BrandButton>
        )}
      </div>

      {ultimaGuardada && editor.modo === "cerrado" && (
        <p
          role="status"
          className="rounded-[10px] border border-brand-orange/20 bg-brand-orange/10 px-4 py-3 font-body text-sm text-foreground"
        >
          Grilla guardada: {ultimaGuardada.motivo ?? "sin motivo"} · {formatFecha(ultimaGuardada.desde)} →{" "}
          {formatFecha(ultimaGuardada.hasta)}
          {ultimaGuardada.advertencias.length > 0
            ? ` · ${ultimaGuardada.advertencias.length} advertencia(s) de cobertura registradas.`
            : " · sin advertencias."}
        </p>
      )}

      {puedeEditar && editor.modo !== "cerrado" && (
        <VarianteEditor
          variante={editor.modo === "edicion" ? editor.variante : null}
          precargaInicial={editor.modo === "alta" ? editor.precarga : null}
          casillas={casillas}
          titular={titular}
          users={users}
          onClose={() => setEditor({ modo: "cerrado" })}
          onSaved={(guardada) => {
            setUltimaGuardada(guardada);
            setEditor({ modo: "cerrado" });
            void load();
          }}
        />
      )}

      <div className="flex flex-wrap items-end gap-3">
        <SegmentedControl
          label="Filtrar por estado"
          size="sm"
          options={FILTROS}
          value={filtro}
          onChange={(v) => setFiltro(v as typeof filtro)}
        />
      </div>

      {variantes === null && !error && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 3 }, (_, i) => (
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

      {variantes !== null && !error && (
        <>
          {filtradas.length === 0 ? (
            <BrandEmptyState
              icon={CalendarOff}
              title="No hay grillas de vacaciones"
              description="Creá una para cubrir una ausencia re-cortando franjas sin tocar la grilla titular."
            />
          ) : (
            <VariantesTabla
              rows={filtradas}
              canMutar={puedeEditar}
              onPreview={setPrevisualizando}
              onEdit={(v) => setEditor({ modo: "edicion", variante: v })}
              onCancel={setCancelando}
            />
          )}
          <p className="rounded-[8px] bg-muted/30 px-4 py-3 font-body text-xs text-muted-foreground">
            Al vencer la vigencia, Turnos del día vuelve automáticamente a la grilla titular. Las grillas
            de vacaciones no modifican la Configuración de Turnos ni su historial; cancelar es la única
            reversión anticipada y queda registrada.
          </p>
        </>
      )}

      {previsualizando && (
        <VariantePreviewModal
          variante={previsualizando}
          ordenCasillas={casillas.map((c) => c.nombre)}
          onClose={() => setPrevisualizando(null)}
        />
      )}

      {cancelando && (
        <BrandModal isOpen onClose={() => setCancelando(null)} title="Cancelar grilla de vacaciones" widthPx={460}>
          <p className="font-body text-sm text-foreground">
            ¿Cancelar la grilla{" "}
            <span className="font-semibold">
              {cancelando.motivo ?? `${formatFecha(cancelando.desde)} → ${formatFecha(cancelando.hasta)}`}
            </span>
            ? Turnos del día vuelve a la grilla titular de inmediato. Queda registrada como cancelada,
            no se borra.
          </p>
          <div className="mt-5 flex justify-end gap-2">
            <BrandButton variant="outline" onClick={() => setCancelando(null)}>
              Volver
            </BrandButton>
            <BrandButton
              onClick={handleCancelar}
              loading={cancelandoBusy}
              className="bg-destructive hover:bg-destructive/90"
            >
              Cancelar grilla
            </BrandButton>
          </div>
        </BrandModal>
      )}
    </div>
  );
}
