"use client";

import { useId, useState, type ReactNode } from "react";
import { AlertTriangle, Loader2, Trash2 } from "lucide-react";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";

/** Modal de confirmación del Patrón 6 del handoff, montado sobre `BrandModal`
 * (que ya aporta el chrome de marca: radio 16px, título Montserrat 800, ✕,
 * focus trap y Escape). Acá va SOLO el cuerpo y el footer de cada variante.
 *
 *  - `simple`: descripción plana, botón primario naranja.
 *  - `warning`: bloque amarillo tintado con ícono en círculo, botón `#eab308`.
 *  - `destructive`: bloque rojo + input de confirmación obligatorio; el botón
 *    rojo arranca deshabilitado y solo se habilita cuando el texto tipeado
 *    coincide EXACTO con `confirmText` (comparación case-sensitive, igual que
 *    el mockup: "Escribí ELIMINAR para confirmar").
 *
 * Los colores de las variantes son literales del handoff a propósito: son
 * semáforo, no tokens de tema. La card sí es dark-aware porque la hereda de
 * `BrandModal`.
 */
export type ConfirmationVariant = "simple" | "warning" | "destructive";

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  variant?: ConfirmationVariant;
  /** Cuerpo del modal. Texto plano o JSX con `<strong>` para resaltar. */
  children: ReactNode;
  /** Label del botón primario. */
  confirmLabel?: string;
  cancelLabel?: string;
  /** Palabra que hay que tipear en la variante destructiva. Default `ELIMINAR`. */
  confirmText?: string;
  /** Deshabilita el botón primario y muestra spinner mientras corre la acción. */
  loading?: boolean;
  /** Error a mostrar arriba del cuerpo (lo pinta `BrandModal`). */
  error?: string | null;
  /** Contenido extra entre el cuerpo y el footer (campos del modal, p.ej. la
   * fecha de corte o el motivo del descarte). */
  extra?: ReactNode;
  widthPx?: number;
}

const variantBlockClasses: Record<Exclude<ConfirmationVariant, "simple">, string> = {
  warning: "bg-[rgba(234,179,8,.08)] border-[rgba(234,179,8,.3)] text-[#92400e] dark:text-[#fde047]",
  destructive:
    "bg-[rgba(239,68,68,.07)] border-[rgba(239,68,68,.25)] text-[#991b1b] dark:text-[#fca5a5]",
};

const variantIconClasses: Record<Exclude<ConfirmationVariant, "simple">, string> = {
  warning: "bg-[rgba(234,179,8,.15)] text-[#eab308]",
  destructive: "bg-[rgba(239,68,68,.12)] text-[#ef4444]",
};

const variantButtonClasses: Record<ConfirmationVariant, string> = {
  simple: "bg-brand-orange text-white hover:bg-brand-orange-hover",
  warning: "bg-[#eab308] text-white hover:bg-[#ca9a04]",
  destructive: "bg-[#ef4444] text-white hover:bg-[#dc2626]",
};

export function ConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  variant = "simple",
  children,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  confirmText = "ELIMINAR",
  loading = false,
  error = null,
  extra,
  widthPx = 420,
}: ConfirmationModalProps) {
  const [typed, setTyped] = useState("");
  const inputId = useId();

  // Cada apertura arranca con el input vacío: si no, reabrir el modal deja el
  // botón destructivo ya habilitado sin que el usuario reconfirme nada. Se
  // resetea durante el render (patrón "ajustar estado al cambiar una prop")
  // en vez de en un efecto — misma forma que el resync de `sidebar.tsx`.
  const [prevOpen, setPrevOpen] = useState(isOpen);
  if (isOpen !== prevOpen) {
    setPrevOpen(isOpen);
    if (isOpen) setTyped("");
  }

  const needsTyping = variant === "destructive";
  const confirmEnabled = !loading && (!needsTyping || typed === confirmText);
  const Icon = variant === "destructive" ? Trash2 : AlertTriangle;

  return (
    <BrandModal isOpen={isOpen} onClose={onClose} title={title} widthPx={widthPx} error={error}>
      <div className="flex flex-col gap-[18px]">
        {variant === "simple" ? (
          <div className="font-body text-sm leading-[1.55] text-muted-foreground">{children}</div>
        ) : (
          <div
            className={cn(
              "flex gap-3.5 rounded-[10px] border p-3.5",
              variantBlockClasses[variant],
            )}
          >
            <span
              className={cn(
                "flex h-9 w-9 flex-none items-center justify-center rounded-full",
                variantIconClasses[variant],
              )}
            >
              <Icon className="h-[18px] w-[18px]" aria-hidden="true" />
            </span>
            <div className="font-body text-[13.5px] leading-[1.55]">{children}</div>
          </div>
        )}

        {extra}

        {needsTyping && (
          <div className="flex flex-col gap-1.5">
            <label htmlFor={inputId} className="sr-only">
              Escribí {confirmText} para confirmar
            </label>
            <input
              id={inputId}
              value={typed}
              onChange={(event) => setTyped(event.target.value)}
              placeholder={`Escribí ${confirmText} para confirmar`}
              autoComplete="off"
              className="rounded-[8px] border-[1.5px] border-[rgba(239,68,68,.4)] bg-card px-3 py-2.5 font-body text-sm text-foreground outline-none focus:border-[#ef4444]"
            />
          </div>
        )}

        <div className="flex gap-2.5">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className={brandButtonClasses({
              variant: "outline",
              className: "flex-1 rounded-[8px] py-[11px]",
            })}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={!confirmEnabled}
            className={cn(
              "flex flex-1 items-center justify-center gap-2 rounded-[8px] py-[11px] font-body text-sm font-bold transition-colors disabled:pointer-events-none disabled:opacity-50",
              variantButtonClasses[variant],
            )}
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
            {confirmLabel}
          </button>
        </div>
      </div>
    </BrandModal>
  );
}
