"use client";

import { useCallback, useEffect, useState } from "react";
import { ChevronLeft, MapPin, Plus, Ticket, Users } from "lucide-react";
import { toast } from "sonner";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { BrandButton, BrandEmptyState, BrandSkeleton, brandButtonClasses } from "@/shared/components/ui/brand-form";
import { insumosApi } from "../../api/insumos-api";
import type { CustomerRow, SdsContactRow, ZoneContactRow } from "../../types";
import { ConfirmationModal } from "../shared";
import { ContactForm, EMPTY_CONTACT } from "./contact-form";
import { ContactsImportModal } from "./contacts-import-modal";
import { ImportFromSupplyModal } from "./import-from-supply-modal";
import { SDS_PILOT_IDS, SdsContactsSection } from "./sds-contacts-section";
import { ZoneContactCard } from "./zone-contact-card";

type View = "list" | "add" | "edit";

function errorMsg(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback;
}

interface ContactsModalProps {
  customer: CustomerRow | null;
  onClose: () => void;
  onContactsChanged: (customerId: number, hasContacts: boolean) => void;
  /** Gatea la aparición de "Importar desde pedido" e "Importar desde SDS".
   * El preview pide `insumos:view` y el apply `insumos:update` en el
   * backend, pero previsualizar sin poder aplicar no sirve para nada en esta
   * UI — un solo flag gatea ambos botones. */
  canUpdate: boolean;
}

/** Modal de gestión de contactos por zona de un cliente.
 * Permite crear, editar y eliminar zonas. Para el cliente piloto (8255) muestra
 * además los contactos detectados en el PortalWeb SDS (solo lectura). */
export function ContactsModal({ customer, onClose, onContactsChanged, canUpdate }: ContactsModalProps) {
  const [contacts, setContacts] = useState<ZoneContactRow[]>([]);
  const [sdsContacts, setSdsContacts] = useState<SdsContactRow[]>([]);
  const [loadingContacts, setLoadingContacts] = useState(false);
  const [contactsError, setContactsError] = useState<string | null>(null);
  const [view, setView] = useState<View>("list");
  const [editingRow, setEditingRow] = useState<ZoneContactRow | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [confirmDeleteZone, setConfirmDeleteZone] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [importFromSupplyOpen, setImportFromSupplyOpen] = useState(false);
  const [importSdsOpen, setImportSdsOpen] = useState(false);

  const customerId = customer?.customer_id ?? null;
  const isOpen = customer !== null;

  const loadContacts = useCallback(async (id: number) => {
    // Resetear el estado antes de cargar (se ejecuta dentro de useCallback, no
    // directamente en el body del effect — mismo patrón que use-new-devices.ts).
    setContacts([]);
    setSdsContacts([]);
    setView("list");
    setEditingRow(null);
    setSaveError(null);
    setLoadingContacts(true);
    setContactsError(null);
    try {
      const data = await insumosApi.getContacts(id);
      setContacts(data);
      if (SDS_PILOT_IDS.has(id)) {
        try {
          const sds = await insumosApi.getSdsContacts(id);
          setSdsContacts(sds);
        } catch {
          setSdsContacts([]);
        }
      }
    } catch (err: unknown) {
      setContactsError(errorMsg(err, "No se pudieron cargar los contactos."));
    } finally {
      setLoadingContacts(false);
    }
  }, []);

  useEffect(() => {
    if (!customerId) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadContacts(customerId);
  }, [customerId, loadContacts]);

  const handleSave = useCallback(
    async (row: ZoneContactRow) => {
      if (!customerId) return;
      setSaving(true);
      setSaveError(null);
      try {
        await insumosApi.putContact(customerId, row);
        setContacts((prev) => {
          const exists = prev.some((c) => c.zone === row.zone);
          return exists ? prev.map((c) => (c.zone === row.zone ? row : c)) : [...prev, row];
        });
        onContactsChanged(customerId, true);
        setView("list");
        toast.success(
          view === "add" ? `Zona "${row.zone}" agregada.` : `Zona "${row.zone}" actualizada.`,
        );
      } catch (err: unknown) {
        setSaveError(errorMsg(err, "No se pudo guardar el contacto."));
      } finally {
        setSaving(false);
      }
    },
    [customerId, view, onContactsChanged],
  );

  const handleDelete = useCallback(async () => {
    if (!customerId || !confirmDeleteZone) return;
    setDeleting(true);
    try {
      await insumosApi.deleteContact(customerId, confirmDeleteZone);
      const remaining = contacts.filter((c) => c.zone !== confirmDeleteZone);
      setContacts(remaining);
      onContactsChanged(customerId, remaining.length > 0);
      setConfirmDeleteZone(null);
      toast.success(`Zona "${confirmDeleteZone}" eliminada.`);
    } catch (err: unknown) {
      toast.error(errorMsg(err, "No se pudo eliminar la zona."));
    } finally {
      setDeleting(false);
    }
  }, [customerId, confirmDeleteZone, contacts, onContactsChanged]);

  // Mismo patrón inmutable que `handleSave`: el backend devuelve el
  // `ZoneContactOut` exacto que escribió, así que no hace falta refetch acá.
  const handleImportedFromSupply = useCallback(
    (row: ZoneContactRow) => {
      if (!customerId) return;
      setContacts((prev) => {
        const exists = prev.some((c) => c.zone === row.zone);
        return exists ? prev.map((c) => (c.zone === row.zone ? row : c)) : [...prev, row];
      });
      onContactsChanged(customerId, true);
    },
    [customerId, onContactsChanged],
  );

  // El apply masivo re-resuelve del lado del servidor: acá SIEMPRE refetch,
  // nunca update optimista.
  const handleSdsImportApplied = useCallback(() => {
    if (!customerId) return;
    void loadContacts(customerId);
    onContactsChanged(customerId, true);
  }, [customerId, loadContacts, onContactsChanged]);

  const title =
    view === "list"
      ? `Contactos — ${customer?.name ?? ""}`
      : view === "add"
        ? "Agregar zona"
        : `Editar zona "${editingRow?.zone ?? ""}"`;

  return (
    <>
      <BrandModal isOpen={isOpen} onClose={onClose} title={title} widthPx={680}>
        {view === "list" ? (
          <div className="flex flex-col gap-4">
            <div className="flex flex-wrap justify-end gap-2">
              {canUpdate && (
                <>
                  <button
                    type="button"
                    onClick={() => setImportSdsOpen(true)}
                    className={brandButtonClasses({ variant: "outline", size: "sm" })}
                  >
                    <Users className="h-3.5 w-3.5" />
                    Importar desde SDS
                  </button>
                  <button
                    type="button"
                    onClick={() => setImportFromSupplyOpen(true)}
                    className={brandButtonClasses({ variant: "outline", size: "sm" })}
                  >
                    <Ticket className="h-3.5 w-3.5" />
                    Importar desde pedido
                  </button>
                </>
              )}
              <BrandButton size="sm" onClick={() => { setEditingRow(null); setSaveError(null); setView("add"); }}>
                <Plus className="h-3.5 w-3.5" />
                Agregar zona
              </BrandButton>
            </div>

            {loadingContacts && (
              <div className="flex flex-col gap-2">
                {[0, 1, 2].map((i) => <BrandSkeleton key={i} className="h-14 w-full" />)}
              </div>
            )}

            {contactsError && (
              <div className="rounded-[8px] border border-[rgba(239,68,68,.25)] bg-[rgba(239,68,68,.07)] px-3 py-2.5 font-body text-sm text-[#991b1b] dark:text-[#fca5a5]">
                {contactsError}
              </div>
            )}

            {!loadingContacts && !contactsError && contacts.length === 0 && (
              <BrandEmptyState icon={MapPin} title="Sin zonas configuradas." description="Usá «Agregar zona» para definir el primer contacto." />
            )}

            {contacts.map((contact) => (
              <ZoneContactCard
                key={contact.zone}
                contact={contact}
                onEdit={(c) => { setEditingRow(c); setSaveError(null); setView("edit"); }}
                onDelete={(zone) => setConfirmDeleteZone(zone)}
              />
            ))}

            <SdsContactsSection customerId={customerId} sdsContacts={sdsContacts} />
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <button
              type="button"
              onClick={() => setView("list")}
              className="flex w-fit cursor-pointer items-center gap-1 font-body text-xs text-muted-foreground hover:text-foreground"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
              Volver a la lista
            </button>
            <ContactForm
              mode={view}
              initial={editingRow ?? EMPTY_CONTACT}
              saving={saving}
              error={saveError}
              onSave={(row) => void handleSave(row)}
              onCancel={() => setView("list")}
            />
          </div>
        )}
      </BrandModal>

      <ConfirmationModal
        isOpen={confirmDeleteZone !== null}
        onClose={() => setConfirmDeleteZone(null)}
        onConfirm={() => void handleDelete()}
        title={`Eliminar zona "${confirmDeleteZone ?? ""}"`}
        variant="destructive"
        confirmText="ELIMINAR"
        confirmLabel="Eliminar"
        loading={deleting}
      >
        Se eliminarán los datos de contacto de la zona <strong>{confirmDeleteZone}</strong>. Esta
        acción no se puede deshacer.
      </ConfirmationModal>

      <ImportFromSupplyModal
        isOpen={importFromSupplyOpen}
        onClose={() => setImportFromSupplyOpen(false)}
        customerId={customerId}
        onImported={handleImportedFromSupply}
      />

      <ContactsImportModal
        isOpen={importSdsOpen}
        onClose={() => setImportSdsOpen(false)}
        customerId={customerId}
        customerName={customer?.name ?? ""}
        onApplied={handleSdsImportApplied}
      />
    </>
  );
}
