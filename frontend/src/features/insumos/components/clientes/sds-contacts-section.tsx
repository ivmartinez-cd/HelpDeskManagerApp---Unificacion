import type { SdsContactRow } from "../../types";

/** Clientes con acceso al piloto de "contactos detectados en SDS". */
export const SDS_PILOT_IDS = new Set([8255]);

interface SdsContactsSectionProps {
  customerId: number | null;
  sdsContacts: SdsContactRow[];
}

/** Bloque "Detectados en SDS (solo lectura)" de la vista `list` del modal de
 * Contactos — solo se muestra para el cliente piloto y cuando hay datos. */
export function SdsContactsSection({ customerId, sdsContacts }: SdsContactsSectionProps) {
  if (!SDS_PILOT_IDS.has(customerId ?? -1) || sdsContacts.length === 0) return null;
  return (
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
  );
}
