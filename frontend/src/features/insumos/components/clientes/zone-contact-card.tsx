import { Trash2 } from "lucide-react";
import { BrandButton } from "@/shared/components/ui/brand-form";
import type { ZoneContactRow } from "../../types";
import { ContactSummary } from "./contact-summary";

interface ZoneContactCardProps {
  contact: ZoneContactRow;
  onEdit: (contact: ZoneContactRow) => void;
  onDelete: (zone: string) => void;
}

/** Card visual de una zona en la vista `list` del modal de Contactos, con los
 * resúmenes de Solicitante/Destinatario y las acciones de editar/eliminar. */
export function ZoneContactCard({ contact, onEdit, onDelete }: ZoneContactCardProps) {
  return (
    <div className="rounded-[10px] border border-border bg-muted/40 p-4">
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="font-body text-sm font-bold text-foreground">{contact.zone}</span>
        <div className="flex gap-1.5">
          <BrandButton size="sm" variant="outline" onClick={() => onEdit(contact)}>
            Editar
          </BrandButton>
          <button
            type="button"
            onClick={() => onDelete(contact.zone)}
            className="flex h-7 w-7 cursor-pointer items-center justify-center rounded-[6px] border border-[rgba(239,68,68,.3)] text-[#ef4444] transition-colors hover:bg-[rgba(239,68,68,.08)]"
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
  );
}
