"use client";

import { useMemo, useState } from "react";
import { Info, RefreshCw, ShieldOff, Trash2, WifiOff } from "lucide-react";
import { BrandButton, BrandEmptyState, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { useSession } from "@/services/session-provider";
import { ConfirmationModal, StatusBadge } from "../shared";
import { formatArgTime } from "../../utils/format";
import { compareSortValues, useTableSort } from "../../hooks/use-table-sort";
import { useOfflineDevices } from "../../hooks/use-offline-devices";
import { OutageBanner } from "./outage-banner";
import { OfflineSection } from "./offline-section";
import { OfflineHelpModal } from "./offline-help-modal";
import {
  groupKeyOf,
  offlineHaystack,
  offlineSortValue,
  OFFLINE_DESC_FIRST,
  OFFLINE_GROUP_ORDER,
  OFFLINE_SORT_KEYS,
  OFFLINE_SORT_STORAGE_KEY,
  type OfflineGroup,
  type OfflineSortKey,
} from "./offline-utils";

/** Pantalla Equipos Offline: equipos sin reportar +72hs, candidatos a baja en
 * SDS tras verificación contra Canal Directo. Agrupa en 6 secciones colapsables,
 * selección múltiple con baja masiva (solo `deletable`), y banner de caídas de
 * colector con 3 niveles de certeza. */

export function OfflineDevicesView() {
  const { can, user } = useSession();
  const canUpdate = user.isSuperadmin || can("insumos", "update");
  const canDelete = user.isSuperadmin || can("insumos", "delete");

  const {
    rows,
    outages,
    candidateCount,
    loading,
    loadError,
    lastUpdatedAt,
    verifying,
    deleting,
    busyDeviceId,
    setDismissed,
    verify,
    deleteDevices,
  } = useOfflineDevices();

  const [query, setQuery] = useState("");
  const [showDismissed, setShowDismissed] = useState(false);

  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [verifyModalOpen, setVerifyModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [helpModalOpen, setHelpModalOpen] = useState(false);

  const { sort, toggleSort } = useTableSort<OfflineSortKey>({
    initial: { key: "daysOffline", direction: "desc" },
    keys: OFFLINE_SORT_KEYS,
    descFirstKeys: OFFLINE_DESC_FIRST,
    storageKey: OFFLINE_SORT_STORAGE_KEY,
  });

  const filteredRows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return rows.filter((row) => {
      if (!showDismissed && row.offlineDismissed) return false;
      if (needle && !offlineHaystack(row).includes(needle)) return false;
      return true;
    });
  }, [rows, query, showDismissed]);

  const sortedRows = useMemo(
    () =>
      [...filteredRows].sort((a, b) =>
        compareSortValues(offlineSortValue(a, sort.key), offlineSortValue(b, sort.key), sort.direction),
      ),
    [filteredRows, sort],
  );

  const grouped = useMemo(() => {
    const map = new Map<OfflineGroup, typeof sortedRows>();
    for (const group of OFFLINE_GROUP_ORDER) map.set(group, []);
    for (const row of sortedRows) {
      const key = groupKeyOf(row);
      map.get(key)!.push(row);
    }
    return map;
  }, [sortedRows]);

  const dismissedCount = useMemo(() => rows.filter((r) => r.offlineDismissed).length, [rows]);
  const deletableRows = useMemo(
    () => filteredRows.filter((r) => r.deletable && !r.inMassOutage),
    [filteredRows],
  );

  function toggleSelect(deviceId: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(deviceId)) next.delete(deviceId);
      else next.add(deviceId);
      return next;
    });
  }

  const selectedCount = [...selected].filter((id) => deletableRows.some((r) => r.deviceId === id)).length;

  async function handleVerify() {
    setVerifyModalOpen(false);
    await verify({ limit: 10 });
    setSelected(new Set());
  }

  async function handleDelete() {
    setDeleteModalOpen(false);
    const deviceIds = [...selected].filter((id) => deletableRows.some((r) => r.deviceId === id));
    if (deviceIds.length === 0) return;
    const ok = await deleteDevices({ deviceIds });
    if (ok) setSelected(new Set());
  }

  return (
    <div className="p-6 lg:p-10">
      {/* ─── Encabezado ─────────────────────────────────────────────── */}
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="font-heading text-2xl font-extrabold text-foreground">
              Equipos offline
            </h1>
            <StatusBadge tone={candidateCount > 0 ? "activo" : "ok"}>
              {candidateCount} candidato{candidateCount === 1 ? "" : "s"} a baja
            </StatusBadge>
            <button
              type="button"
              onClick={() => setHelpModalOpen(true)}
              title="Ver detalles sobre la verificación y bajas"
              className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-2.5 py-1 font-body text-xs font-medium text-muted-foreground shadow-sm transition-colors hover:bg-muted hover:text-foreground"
            >
              <Info className="h-3.5 w-3.5" />
              ¿Cómo funciona?
            </button>
          </div>
          <p className="mt-1 font-body text-sm text-muted-foreground">
            Equipos sin reportar +72hs. Verificar contra Canal Directo antes de dar de baja.
            {lastUpdatedAt && ` Actualizado ${formatArgTime(lastUpdatedAt.toISOString())}.`}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {canDelete && selectedCount > 0 && (
            <BrandButton
              onClick={() => setDeleteModalOpen(true)}
              loading={deleting}
              className="bg-[#ef4444] text-white hover:bg-[#dc2626]"
            >
              {!deleting && <Trash2 className="h-4 w-4" />}
              Dar de baja ({selectedCount})
            </BrandButton>
          )}
          <BrandButton
            onClick={() => setVerifyModalOpen(true)}
            loading={verifying}
            disabled={!canUpdate}
            title={canUpdate ? undefined : "Sin permiso para verificar equipos"}
            variant="outline"
          >
            {!verifying && <RefreshCw className="h-4 w-4" />}
            Verificar
          </BrandButton>
        </div>
      </div>

      {/* ─── Barra de filtros ────────────────────────────────────────── */}
      <div className="mb-5 flex flex-wrap items-center gap-3">
        <div className="relative min-w-[200px] flex-1">
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar por serie, modelo, cliente, zona…"
            className="w-full rounded-[8px] border border-border bg-card px-3 py-2 font-body text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-brand-orange"
          />
        </div>
        <label className="flex cursor-pointer items-center gap-2 font-body text-sm text-muted-foreground">
          <input
            type="checkbox"
            checked={showDismissed}
            onChange={(e) => setShowDismissed(e.target.checked)}
            className="accent-brand-orange"
          />
          Mostrar descartados{dismissedCount > 0 ? ` (${dismissedCount})` : ""}
        </label>
      </div>

      {/* ─── Banner de caídas de colector ────────────────────────────── */}
      <OutageBanner outages={outages} />

      {/* ─── Error ───────────────────────────────────────────────────── */}
      {loadError && (
        <div className="mb-4 rounded-[10px] border border-[rgba(239,68,68,.25)] bg-[rgba(239,68,68,.07)] px-4 py-3 font-body text-sm text-[#991b1b] dark:text-[#fca5a5]">
          {loadError}
        </div>
      )}

      {/* ─── Contenido principal ─────────────────────────────────────── */}
      {loading ? (
        <div className="flex flex-col gap-3">
          {[0, 1, 2, 3].map((index) => (
            <BrandSkeleton key={index} className="h-16 w-full" />
          ))}
        </div>
      ) : rows.length === 0 ? (
        <BrandEmptyState
          icon={WifiOff}
          title="No hay equipos offline."
          description="Todos los equipos están reportando al colector dentro del umbral de 72hs."
        />
      ) : filteredRows.length === 0 ? (
        <BrandEmptyState
          icon={ShieldOff}
          title="Ningún equipo coincide con los filtros."
          description="Probá limpiar la búsqueda o mostrar los descartados."
        />
      ) : (
        <div className="flex flex-col gap-3">
          {OFFLINE_GROUP_ORDER.map((group) => {
            const groupRows = grouped.get(group) ?? [];
            return (
              <OfflineSection
                key={group}
                group={group}
                rows={groupRows}
                sort={sort}
                onToggleSort={toggleSort}
                canUpdate={canUpdate}
                canDelete={canDelete}
                busyDeviceId={busyDeviceId}
                selected={selected}
                onToggleSelect={toggleSelect}
                onToggleDismissed={(device, dismissed) => void setDismissed(device, dismissed)}
              />
            );
          })}

          <p className="mt-1 font-body text-xs text-muted-foreground">
            Mostrando {filteredRows.length} de {rows.length} equipo(s). La lista se actualiza sola
            cada 5 minutos.
          </p>
        </div>
      )}

      {/* ─── Modal verificar ─────────────────────────────────────────── */}
      <ConfirmationModal
        isOpen={verifyModalOpen}
        onClose={() => setVerifyModalOpen(false)}
        onConfirm={() => void handleVerify()}
        title="Verificar equipos offline"
        confirmLabel="Verificar"
        loading={verifying}
      >
        Se consultarán hasta <strong>10 equipos pendientes</strong> contra Canal Directo (SOAP)
        para determinar su veredicto. Los resultados actualizan la lista automáticamente. La
        operación puede demorar unos segundos.
      </ConfirmationModal>

      {/* ─── Modal dar de baja ───────────────────────────────────────── */}
      <ConfirmationModal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={() => void handleDelete()}
        title="Dar de baja en SDS"
        variant="destructive"
        confirmLabel="Dar de baja"
        loading={deleting}
      >
        Se darán de baja <strong>{selectedCount} equipo(s)</strong> seleccionado(s) en el
        PortalWeb de SDS. Esta operación es <strong>irreversible</strong>. Solo se procesan
        los equipos con veredicto «En bodega» — el resto se omite.{" "}
        {/* El env SDS_DELETE_DRY_RUN=true (default) hace que la baja sea auditada
            pero no ejecutada realmente en el portal. */}
        Revisá que los equipos sean correctos antes de confirmar.
      </ConfirmationModal>

      {/* ─── Modal de ayuda ──────────────────────────────────────────── */}
      <OfflineHelpModal isOpen={helpModalOpen} onClose={() => setHelpModalOpen(false)} />
    </div>
  );
}
