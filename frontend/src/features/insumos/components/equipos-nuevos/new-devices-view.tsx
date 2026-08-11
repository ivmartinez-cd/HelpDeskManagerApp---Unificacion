"use client";

import { useMemo, useState } from "react";
import { PrinterCheck, RefreshCw } from "lucide-react";
import { BrandButton, BrandEmptyState, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { useSession } from "@/services/session-provider";
import { ConfirmationModal, StatusBadge } from "../shared";
import { formatArgTime } from "../../utils/format";
import { compareSortValues, useTableSort } from "../../hooks/use-table-sort";
import { useNewDevices } from "../../hooks/use-new-devices";
import { NewDevicesTable } from "./new-devices-table";
import { ALL_YEARS, NewDevicesToolbar } from "./new-devices-toolbar";
import {
  availableYears,
  discoveryYear,
  newDeviceHaystack,
  newDeviceSortValue,
  NEW_DEVICES_SORT_STORAGE_KEY,
  NEW_DEVICE_DESC_FIRST,
  NEW_DEVICE_SORT_KEYS,
  type NewDeviceSortKey,
} from "./new-devices-utils";

/** Pantalla Equipos Nuevos: equipos que Insight ve en clientes habilitados
 * pero que todavía no están monitoreados, así que no generan avisos de
 * insumos. Filtrado y ordenamiento son client-side sobre el listado completo
 * (ver `useNewDevices`).
 *
 * El filtro por año arranca en el año en curso, igual que el legacy: el
 * backlog histórico tapa lo accionable. */

const CURRENT_YEAR = String(new Date().getFullYear());

export function NewDevicesView() {
  const { can, user } = useSession();
  // `can()` solo refleja grants explícitos: un superadmin llega con la lista de
  // permisos vacía y sin este OR no podría ni sincronizar ni ignorar equipos.
  const canUpdate = user.isSuperadmin || can("insumos", "update");
  const {
    rows,
    pendingCount,
    loading,
    loadError,
    syncing,
    busyDeviceId,
    lastUpdatedAt,
    setDismissed,
    sync,
  } = useNewDevices();

  const [query, setQuery] = useState("");
  const [year, setYear] = useState(CURRENT_YEAR);
  const [showDismissed, setShowDismissed] = useState(false);
  const [syncModalOpen, setSyncModalOpen] = useState(false);

  const { sort, toggleSort } = useTableSort<NewDeviceSortKey>({
    initial: { key: "discoveryDate", direction: "desc" },
    keys: NEW_DEVICE_SORT_KEYS,
    descFirstKeys: NEW_DEVICE_DESC_FIRST,
    storageKey: NEW_DEVICES_SORT_STORAGE_KEY,
  });

  const yearOptions = useMemo(() => {
    const options = new Set(availableYears(rows));
    // El año en curso y el elegido siempre están, aunque no haya filas: si no,
    // el `<select>` quedaría en blanco al no encontrar su propio valor.
    options.add(CURRENT_YEAR);
    options.add(year);
    return [...options].sort((a, b) => b.localeCompare(a));
  }, [rows, year]);

  const dismissedCount = useMemo(() => rows.filter((row) => row.dismissed).length, [rows]);

  const visibleRows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const filtered = rows.filter((row) => {
      if (!showDismissed && row.dismissed) return false;
      if (year !== ALL_YEARS && discoveryYear(row) !== year) return false;
      if (needle && !newDeviceHaystack(row).includes(needle)) return false;
      return true;
    });
    return filtered.sort((a, b) =>
      compareSortValues(
        newDeviceSortValue(a, sort.key),
        newDeviceSortValue(b, sort.key),
        sort.direction,
      ),
    );
  }, [rows, query, year, showDismissed, sort]);

  const hasFilters = query.trim() !== "" || year !== ALL_YEARS || !showDismissed;

  return (
    <div className="p-6 lg:p-10">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="font-heading text-2xl font-extrabold text-foreground">Equipos nuevos</h1>
            <StatusBadge tone={pendingCount > 0 ? "activo" : "ok"}>
              {pendingCount} pendiente{pendingCount === 1 ? "" : "s"}
            </StatusBadge>
          </div>
          <p className="mt-1 font-body text-sm text-muted-foreground">
            Equipos detectados por Insight en clientes habilitados que todavía no están
            monitoreados.
            {lastUpdatedAt && ` Actualizado ${formatArgTime(lastUpdatedAt.toISOString())}.`}
          </p>
        </div>
        <BrandButton
          onClick={() => setSyncModalOpen(true)}
          loading={syncing}
          disabled={!canUpdate}
          title={canUpdate ? undefined : "Sin permiso para sincronizar"}
        >
          {!syncing && <RefreshCw className="h-4 w-4" />}
          Sincronizar
        </BrandButton>
      </div>

      <NewDevicesToolbar
        query={query}
        onQueryChange={setQuery}
        year={year}
        years={yearOptions}
        onYearChange={setYear}
        showDismissed={showDismissed}
        onShowDismissedChange={setShowDismissed}
        dismissedCount={dismissedCount}
      />

      {loadError && (
        <div className="mb-4 rounded-[10px] border border-[rgba(239,68,68,.25)] bg-[rgba(239,68,68,.07)] px-4 py-3 font-body text-sm text-[#991b1b] dark:text-[#fca5a5]">
          {loadError}
        </div>
      )}

      {loading ? (
        <div className="flex flex-col gap-2">
          {[0, 1, 2, 3, 4].map((index) => (
            <BrandSkeleton key={index} className="h-12 w-full" />
          ))}
        </div>
      ) : visibleRows.length === 0 ? (
        <BrandEmptyState
          icon={PrinterCheck}
          title={
            rows.length === 0
              ? "No hay equipos nuevos sin registrar."
              : "Ningún equipo coincide con los filtros."
          }
          description={
            rows.length > 0 && hasFilters
              ? "Probá con «Todos los años», limpiar la búsqueda o mostrar los ignorados."
              : undefined
          }
        />
      ) : (
        <>
          <NewDevicesTable
            rows={visibleRows}
            sort={sort}
            onToggleSort={toggleSort}
            canUpdate={canUpdate}
            busyDeviceId={busyDeviceId}
            onToggleDismissed={(device, dismissed) => void setDismissed(device, dismissed)}
          />
          <p className="mt-3 font-body text-xs text-muted-foreground">
            Mostrando {visibleRows.length} de {rows.length} equipo(s). La lista se actualiza sola
            cada 5 minutos.
          </p>
        </>
      )}

      <ConfirmationModal
        isOpen={syncModalOpen}
        onClose={() => setSyncModalOpen(false)}
        onConfirm={() => {
          setSyncModalOpen(false);
          void sync();
        }}
        title="Sincronizar equipos nuevos"
        confirmLabel="Sincronizar"
        loading={syncing}
      >
        Se consulta el inventario de Insight de todos los clientes habilitados y se actualiza la
        lista de equipos sin monitorear. Puede demorar unos segundos.
      </ConfirmationModal>
    </div>
  );
}
