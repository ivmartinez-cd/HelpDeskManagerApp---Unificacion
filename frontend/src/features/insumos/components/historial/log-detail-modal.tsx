"use client";

import { ConfirmationModal } from "../shared";
import { EMPTY_VALUE } from "../../utils/format";

/** Modal de "log completo" del handoff (bloque 6, Historial): variante simple
 * del Patrón 6 con una ficha de campos arriba y el output del proceso en un
 * `<pre>` monoespacio. Sin acción secundaria — el único botón es "Cerrar"
 * (`hideCancel`), porque no hay nada que confirmar.
 *
 * Lo comparten la tabla de auditoría (columna "Detalles") y la de mails (el
 * texto de error de un envío fallido). */

export interface LogDetailField {
  label: string;
  value: string;
}

interface LogDetailModalProps {
  isOpen: boolean;
  title: string;
  fields: LogDetailField[];
  /** Cuerpo del log. `null`/vacío muestra el placeholder. */
  output: string | null | undefined;
  outputLabel?: string;
  onClose: () => void;
}

export function LogDetailModal({
  isOpen,
  title,
  fields,
  output,
  outputLabel = "Detalle del proceso",
  onClose,
}: LogDetailModalProps) {
  return (
    <ConfirmationModal
      isOpen={isOpen}
      onClose={onClose}
      onConfirm={onClose}
      title={title}
      variant="simple"
      confirmLabel="Cerrar"
      hideCancel
      widthPx={560}
    >
      <div className="flex flex-col gap-4">
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2.5">
          {fields.map((field) => (
            <div key={field.label} className="flex flex-col gap-0.5">
              <dt className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
                {field.label}
              </dt>
              <dd className="break-words font-body text-[13px] text-foreground">
                {field.value || EMPTY_VALUE}
              </dd>
            </div>
          ))}
        </dl>

        <div className="flex flex-col gap-1.5">
          <span className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            {outputLabel}
          </span>
          <pre className="max-h-[280px] overflow-auto whitespace-pre-wrap break-words rounded-[8px] border border-border bg-muted/40 p-3 font-mono text-[12px] leading-[1.5] text-foreground">
            {output?.trim() ? output : "Sin detalle registrado para este evento."}
          </pre>
        </div>
      </div>
    </ConfirmationModal>
  );
}
