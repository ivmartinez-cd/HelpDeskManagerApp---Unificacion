"use client";

import { Check, Loader2, Phone } from "lucide-react";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import type { CustomerRow } from "../../types";

interface CustomersTableProps {
  rows: CustomerRow[];
  canUpdate: boolean;
  busyId: number | null;
  notifyBusyId: number | null;
  onToggle: (row: CustomerRow, enabled: boolean) => void;
  onToggleClientMail: (row: CustomerRow, enabled: boolean) => void;
  onOpenContacts: (row: CustomerRow) => void;
}

/** Tabla de clientes con toggle de monitoreo, aviso por mail al cliente y
 * acceso a contactos por zona. */
export function CustomersTable({
  rows,
  canUpdate,
  busyId,
  notifyBusyId,
  onToggle,
  onToggleClientMail,
  onOpenContacts,
}: CustomersTableProps) {
  return (
    <div className="overflow-x-auto rounded-[10px] border border-border">
      <table className="w-full min-w-[520px]">
        <thead>
          <tr className="border-b border-border bg-muted/50">
            <th className="w-16 px-4 py-3 text-left font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
              Activo
            </th>
            <th className="px-4 py-3 text-left font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
              Cliente
            </th>
            <th className="w-36 px-4 py-3 text-center font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
              Aviso por mail
            </th>
            <th className="w-32 px-4 py-3 text-right font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
              Contactos
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map((row) => {
            const busy = busyId === row.customer_id;
            const notifyBusy = notifyBusyId === row.customer_id;
            return (
              <tr key={row.customer_id} className="hover:bg-muted/30 transition-colors">
                <td className="px-4 py-3">
                  <button
                    type="button"
                    role="switch"
                    aria-checked={row.enabled}
                    disabled={!canUpdate || busy}
                    onClick={() => onToggle(row, !row.enabled)}
                    className={cn(
                      "relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-brand-orange/40 disabled:cursor-not-allowed disabled:opacity-50",
                      row.enabled ? "bg-brand-orange" : "bg-muted-foreground/30",
                    )}
                    title={row.enabled ? "Deshabilitar monitoreo" : "Habilitar monitoreo"}
                  >
                    <span
                      className={cn(
                        "pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out",
                        row.enabled ? "translate-x-4" : "translate-x-0",
                      )}
                    />
                  </button>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    {busy && <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />}
                    <span className="font-body text-sm text-foreground">{row.name}</span>
                    {!row.enabled && (
                      <span className="font-body text-[10px] text-muted-foreground">(deshabilitado)</span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-center">
                  <button
                    type="button"
                    disabled={!canUpdate || notifyBusy}
                    onClick={() => onToggleClientMail(row, !row.client_mail_enabled)}
                    title="Avisá por mail al cliente cuando se carga su pedido"
                    className={cn(
                      "inline-flex cursor-pointer items-center gap-1 rounded-full px-2.5 py-1 font-body text-[10px] font-bold transition-colors disabled:cursor-not-allowed disabled:opacity-50",
                      row.client_mail_enabled
                        ? "bg-[rgba(34,197,94,.1)] text-[#16a34a] dark:text-[#4ade80]"
                        : "bg-muted text-muted-foreground",
                    )}
                  >
                    {notifyBusy && <Loader2 className="h-3 w-3 animate-spin" />}
                    {row.client_mail_enabled && !notifyBusy && (
                      <Check className="h-3 w-3" aria-hidden="true" />
                    )}
                    {row.client_mail_enabled ? "Activado" : "Desactivado"}
                  </button>
                </td>
                <td className="px-4 py-3 text-right">
                  <BrandButton
                    size="sm"
                    variant="outline"
                    onClick={() => onOpenContacts(row)}
                    title="Ver y editar contactos por zona"
                  >
                    <Phone className="h-3.5 w-3.5" />
                    {row.has_contacts ? "Ver" : "Configurar"}
                  </BrandButton>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
