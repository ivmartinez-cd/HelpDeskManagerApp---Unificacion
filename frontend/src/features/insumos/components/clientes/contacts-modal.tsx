"use client";

import { useCallback, useEffect, useState } from "react";
import { ChevronLeft, MapPin, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { BrandButton, BrandEmptyState, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { insumosApi } from "../../api/insumos-api";
import type { CustomerRow, SdsContactRow, ZoneContactRow } from "../../types";
import { ConfirmationModal } from "../shared";
import { ContactForm, EMPTY_CONTACT } from "./contact-form";

/** Clientes con acceso al piloto de "contactos detectados en SDS". */
const SDS_PILOT_IDS = new Set([8255]);

type View = "list" | "add" | "edit";

function errorMsg(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback;
}

interface ContactsModalProps {
  customer: CustomerRow | null;
  onClose: () => void;
  onContactsChanged: (customerId: number, hasContacts: boolean) => void;
}

/** Modal de gestión de contactos por zona de un cliente.
 * Permite crear, editar y eliminar zonas. Para el cliente piloto (8255) muestra
 * además los contactos detectados en el PortalWeb SDS (solo lectura). */
export function ContactsModal({ customer, onClose, onContactsChanged }: ContactsModalProps) {
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
            <div className="flex justify-end">
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
              <div key={contact.zone} className="rounded-[10px] border border-border bg-muted/40 p-4">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <span className="font-body text-sm font-bold text-foreground">{contact.zone}</span>
                  <div className="flex gap-1.5">
                    <BrandButton size="sm" variant="outline" onClick={() => { setEditingRow(contact); setSaveError(null); setView("edit"); }}>
                      Editar
                    </BrandButton>
                    <button
                      type="button"
                      onClick={() => setConfirmDeleteZone(contact.zone)}
                      className="flex h-7 w-7 items-center justify-center rounded-[6px] border border-[rgba(239,68,68,.3)] text-[#ef4444] transition-colors hover:bg-[rgba(239,68,68,.08)]"
                      title="Eliminar zona"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                  <ContactSummary label="Solicitante" apellido={contact.sol_apellido} nombre={contact.sol_nombre} email={contact.sol_email} telefono={contact.sol_telefono} />
                  <ContactSummary label="Destinatario" apellido={contact.dest_apellido} nombre={contact.dest_nombre} email={contact.dest_email} telefono={contact.dest_telefono} />
                </div>
                {contact.observaciones && (
                  <p className="mt-2 font-body text-xs text-muted-foreground">{contact.observaciones}</p>
                )}
              </div>
            ))}

            {SDS_PILOT_IDS.has(customerId ?? -1) && sdsContacts.length > 0 && (
              <div className="mt-2 border-t border-border pt-4">
                <p className="mb-2 font-body text-xs font-bold uppercase tracking-wide text-muted-foreground">
                  Detectados en SDS (solo lectura)
                </p>
                {sdsContacts.map((c, i) => (
                  <div key={i} className="mb-1.5 rounded-[8px] bg-muted/50 px-3 py-2 font-body text-xs text-muted-foreground">
                    <span className="font-bold text-foreground">{c.zone}</span>
                    {" — "}
                    {c.contacto}
                    {c.email ? ` · ${c.email}` : ""}
                    {c.sucursal ? ` (${c.sucursal})` : ""}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <button
              type="button"
              onClick={() => setView("list")}
              className="flex w-fit items-center gap-1 font-body text-xs text-muted-foreground hover:text-foreground"
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
    </>
  );
}

function ContactSummary({
  label,
  apellido,
  nombre,
  email,
  telefono,
}: {
  label: string;
  apellido: string;
  nombre: string;
  email: string;
  telefono: string;
}) {
  const name = [apellido, nombre].filter(Boolean).join(", ");
  return (
    <div>
      <p className="font-body text-[10px] font-bold uppercase tracking-wide text-muted-foreground">{label}</p>
      {name ? <p className="font-body text-xs text-foreground">{name}</p> : null}
      {email ? <p className="font-body text-xs text-muted-foreground">{email}</p> : null}
      {telefono ? <p className="font-body text-xs text-muted-foreground">{telefono}</p> : null}
    </div>
  );
}
