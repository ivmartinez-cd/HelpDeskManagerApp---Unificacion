"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";
import { AlertTriangle, X } from "lucide-react";

interface BrandModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  /** Ancho del modal en px (el handoff usa 420 para el ejemplo de SDS; las
   * herramientas con formularios más largos piden más aire). */
  widthPx?: number;
  error?: string | null;
}

/** Modal con el chrome de marca del design handoff (overlay oscuro, card
 * 16px de radio, título Montserrat) — misma mecánica de accesibilidad que
 * `shared/components/ui/modal.tsx` (focus trap, Escape, aria-modal), pero
 * con la identidad visual de Canal Directo en vez del design system
 * genérico. Usado por las herramientas de Contadores desde que se
 * migraron a modales (ver contadores-hub.tsx).
 *
 * La card usa tokens dark-aware (`bg-card`/`text-foreground`), no colores
 * fijos: el handoff pedía "card blanca" asumiendo tema claro único, pero
 * ahora responde al toggle de tema como el resto de la app. */
export function BrandModal({ isOpen, onClose, title, children, widthPx = 480, error }: BrandModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);
  const titleId = useId();

  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement as HTMLElement;
      const timer = setTimeout(() => {
        if (modalRef.current) {
          const focusableElements = modalRef.current.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
          );
          if (focusableElements.length > 0) {
            (focusableElements[0] as HTMLElement).focus();
          } else {
            modalRef.current.focus();
          }
        }
      }, 100);
      return () => clearTimeout(timer);
    } else if (previousActiveElement.current) {
      previousActiveElement.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4"
      style={{ background: "rgba(20,20,20,.55)" }}
      onClick={onClose}
    >
      <div
        ref={modalRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(e) => e.stopPropagation()}
        style={{ width: widthPx, boxShadow: "0 20px 60px rgba(0,0,0,.25)" }}
        className="flex max-h-[90vh] w-full max-w-[92vw] flex-col overflow-hidden rounded-[16px] bg-card focus:outline-none"
      >
        <div className="flex items-center justify-between px-[30px] pt-7 pb-2">
          <h2
            id={titleId}
            className="font-heading text-[20px] font-extrabold tracking-[.01em] text-foreground"
          >
            {title}
          </h2>
          <button
            onClick={onClose}
            aria-label="Cerrar modal"
            className="rounded-[8px] p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto thin-scrollbar px-[30px] pb-[30px] pt-3">
          {error && (
            <div className="mb-5 flex items-center gap-3 rounded-[10px] border border-destructive/20 bg-destructive/10 p-3 text-destructive">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <p className="font-body text-xs font-semibold leading-tight">{error}</p>
            </div>
          )}
          {children}
        </div>
      </div>
    </div>
  );
}
