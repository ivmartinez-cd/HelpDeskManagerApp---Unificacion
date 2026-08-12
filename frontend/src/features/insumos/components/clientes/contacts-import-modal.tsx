"use client";

import { useState } from "react";
import { Search } from "lucide-react";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { BrandButton, BrandEmptyState, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { selectableImportRow, useContactsImport } from "../../hooks/use-contacts-import";
import { ContactsImportTable } from "./contacts-import-table";

interface ContactsImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  customerId: number | null;
  customerName: string;
  onApplied: () => void;
}

/** Modal de importación masiva de contactos desde el PortalWeb de SDS.
 * El preview es un botón explícito, nunca un fetch automático al abrir: el
 * endpoint scrapea SDS + Insight, es lento y puede fallar entero — ver el
 * comentario largo en `customers_router.py` líneas ~195-213. */
export function ContactsImportModal({
  isOpen,
  onClose,
  customerId,
  customerName,
  onApplied,
}: ContactsImportModalProps) {
  const { rows, selected, loading, applying, error, preview, toggle, toggleAll, apply } =
    useContactsImport(isOpen ? customerId : null, onApplied);

  // Arranca en idle cada vez que el modal se vuelve a abrir — mismo patrón
  // de resync durante el render que usa `confirmation-modal.tsx`.
  const [started, setStarted] = useState(false);
  const [prevOpen, setPrevOpen] = useState(isOpen);
  if (isOpen !== prevOpen) {
    setPrevOpen(isOpen);
    if (isOpen) setStarted(false);
  }

  const selectableCount = rows.filter(selectableImportRow).length;

  function handleClose() {
    setStarted(false);
    onClose();
  }

  return (
    <BrandModal
      isOpen={isOpen}
      onClose={handleClose}
      title={`Importar desde SDS — ${customerName}`}
      widthPx={860}
    >
      {loading ? (
        <div className="flex flex-col gap-2">
          {[0, 1, 2, 3].map((i) => <BrandSkeleton key={i} className="h-12 w-full" />)}
        </div>
      ) : !started ? (
        <div className="flex flex-col items-center justify-center gap-4 py-10">
          <p className="max-w-md text-center font-body text-sm text-muted-foreground">
            Consulta el PortalWeb de SDS y compara los contactos detectados contra los ya
            configurados. Puede tardar — se ejecuta solo cuando lo pedís.
          </p>
          <BrandButton onClick={() => { setStarted(true); void preview(); }}>
            <Search className="h-4 w-4" />
            Previsualizar
          </BrandButton>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {error && (
            <div className="rounded-[8px] border border-[rgba(239,68,68,.25)] bg-[rgba(239,68,68,.07)] px-3 py-2.5 font-body text-sm text-[#991b1b] dark:text-[#fca5a5]">
              {error}
            </div>
          )}

          {!error && rows.length === 0 && (
            <BrandEmptyState
              icon={Search}
              title="Sin zonas detectadas."
              description="El PortalWeb de SDS no devolvió contactos para este cliente."
            />
          )}

          {rows.length > 0 && (
            <ContactsImportTable
              rows={rows}
              selected={selected}
              onToggle={toggle}
              onToggleAll={toggleAll}
            />
          )}

          <div className="flex items-center justify-between gap-3 border-t border-border pt-4">
            <p className="font-body text-xs text-muted-foreground">
              {selected.size} de {selectableCount} zonas seleccionadas
            </p>
            <div className="flex gap-2.5">
              <BrandButton variant="outline" size="sm" onClick={() => void preview()} disabled={applying}>
                Volver a previsualizar
              </BrandButton>
              <BrandButton
                size="sm"
                onClick={() => void apply()}
                loading={applying}
                disabled={selected.size === 0}
              >
                Importar seleccionadas
              </BrandButton>
            </div>
          </div>
        </div>
      )}
    </BrandModal>
  );
}
