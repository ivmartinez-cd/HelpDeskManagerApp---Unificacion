"use client";

import { useMemo, useState } from "react";
import { RefreshCw, Users } from "lucide-react";
import { BrandButton, BrandEmptyState, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { useSession } from "@/services/session-provider";
import { ConfirmationModal } from "../shared/confirmation-modal";
import { StatusBadge } from "../shared/status-badge";
import { useCustomers } from "../../hooks/use-customers";
import type { CustomerRow } from "../../types";
import { ContactsModal } from "./contacts-modal";
import { CustomersTable } from "./customers-table";

export function ClientesView() {
  const { can, user } = useSession();
  const canUpdate = user.isSuperadmin || can("insumos", "update");

  const {
    rows,
    loading,
    loadError,
    busyId,
    syncing,
    bulkLoading,
    toggle,
    bulkToggle,
    sync,
    markHasContacts,
  } = useCustomers();

  const [query, setQuery] = useState("");
  const [syncModalOpen, setSyncModalOpen] = useState(false);
  const [bulkEnableModal, setBulkEnableModal] = useState<boolean | null>(null);
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerRow | null>(null);

  const filteredRows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return rows;
    return rows.filter((r) => r.name.toLowerCase().includes(needle));
  }, [rows, query]);

  const enabledCount = useMemo(() => rows.filter((r) => r.enabled).length, [rows]);

  return (
    <div className="p-6 lg:p-10">
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="font-heading text-2xl font-extrabold text-foreground">Clientes</h1>
            {!loading && (
              <StatusBadge tone={enabledCount > 0 ? "ok" : "neutral"}>
                {enabledCount} de {rows.length} habilitados
              </StatusBadge>
            )}
          </div>
          <p className="mt-1 font-body text-sm text-muted-foreground">
            Clientes de Insight monitoreados por HelpDesk Manager. Solo los habilitados generan
            alertas y avisan sobre equipos nuevos u offline.
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

      {/* Toolbar */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <input
          type="search"
          placeholder="Buscar cliente…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="h-9 w-56 rounded-[8px] border border-border bg-card px-3 font-body text-sm text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40"
        />
        <BrandButton
          size="sm"
          variant="outline"
          onClick={() => setBulkEnableModal(true)}
          disabled={!canUpdate || bulkLoading}
          loading={bulkLoading}
        >
          Habilitar todos
        </BrandButton>
        <BrandButton
          size="sm"
          variant="outline"
          onClick={() => setBulkEnableModal(false)}
          disabled={!canUpdate || bulkLoading}
          loading={bulkLoading}
        >
          Deshabilitar todos
        </BrandButton>
      </div>

      {/* Error */}
      {loadError && (
        <div className="mb-4 rounded-[10px] border border-[rgba(239,68,68,.25)] bg-[rgba(239,68,68,.07)] px-4 py-3 font-body text-sm text-[#991b1b] dark:text-[#fca5a5]">
          {loadError}
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div className="flex flex-col gap-2">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <BrandSkeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : filteredRows.length === 0 ? (
        <BrandEmptyState
          icon={Users}
          title={rows.length === 0 ? "No hay clientes cargados." : "Ningún cliente coincide con la búsqueda."}
          description={rows.length === 0 ? "Usá «Sincronizar» para importar clientes desde Insight." : undefined}
        />
      ) : (
        <>
          <CustomersTable
            rows={filteredRows}
            canUpdate={canUpdate}
            busyId={busyId}
            onToggle={(row, enabled) => void toggle(row, enabled)}
            onOpenContacts={setSelectedCustomer}
          />
          <p className="mt-3 font-body text-xs text-muted-foreground">
            Mostrando {filteredRows.length} de {rows.length} cliente(s).
          </p>
        </>
      )}

      {/* Sync confirm */}
      <ConfirmationModal
        isOpen={syncModalOpen}
        onClose={() => setSyncModalOpen(false)}
        onConfirm={() => { setSyncModalOpen(false); void sync(); }}
        title="Sincronizar clientes"
        confirmLabel="Sincronizar"
        loading={syncing}
      >
        Se consulta el inventario de Insight y se actualizan los clientes de la lista. Los
        clientes existentes no pierden su configuración ni sus contactos.
      </ConfirmationModal>

      {/* Bulk toggle confirm */}
      <ConfirmationModal
        isOpen={bulkEnableModal !== null}
        onClose={() => setBulkEnableModal(null)}
        onConfirm={() => {
          const val = bulkEnableModal;
          setBulkEnableModal(null);
          if (val !== null) void bulkToggle(val);
        }}
        title={bulkEnableModal ? "Habilitar todos los clientes" : "Deshabilitar todos los clientes"}
        variant={bulkEnableModal ? "simple" : "warning"}
        confirmLabel={bulkEnableModal ? "Habilitar todos" : "Deshabilitar todos"}
        loading={bulkLoading}
      >
        {bulkEnableModal
          ? "Se habilitará el monitoreo de todos los clientes en la lista."
          : "Se desactivará el monitoreo de todos los clientes. No se generarán nuevas alertas ni avisos de equipos."}
      </ConfirmationModal>

      {/* Contacts modal */}
      <ContactsModal
        customer={selectedCustomer}
        onClose={() => setSelectedCustomer(null)}
        onContactsChanged={(id, hasContacts) => {
          markHasContacts(id, hasContacts);
        }}
      />
    </div>
  );
}
