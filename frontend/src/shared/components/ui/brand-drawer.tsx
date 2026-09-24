"use client";

import { useEffect, useId, useRef, useSyncExternalStore, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

interface BrandDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  /** Contenido del `<h2>` que nombra el diálogo (`aria-labelledby`). */
  title: ReactNode;
  /** Arriba del título (ej. un chip de estado). */
  eyebrow?: ReactNode;
  /** Debajo del título (línea secundaria). */
  subtitle?: ReactNode;
  /** Pie fijo (no scrollea con el cuerpo). */
  footer?: ReactNode;
  children: ReactNode;
  closeLabel?: string;
}

const FOCUSABLE =
  'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

function focusables(root: HTMLElement): HTMLElement[] {
  return Array.from(root.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
    (el) => el.offsetParent !== null || el === document.activeElement,
  );
}

/** Panel lateral derecho con el chrome de marca (patrón del handoff de
 * Despachados): portal a `document.body`, `role="dialog"` + `aria-modal`,
 * Escape y click en el fondo cierran, foco inicial en "Cerrar panel", Tab
 * atrapado adentro y, al cerrar, el foco vuelve a lo que lo abrió (la fila).
 * Misma mecánica que `brand-modal.tsx` (portal con `useSyncExternalStore`
 * para no romper el SSR). Ancho `min(480px, 100vw)`; cabecera y pie fijos,
 * cuerpo con scroll.
 *
 * Teclado con un modal encima (ej. "Registrar acción" abierto desde el
 * panel): Escape y Tab solo se atienden si el foco está dentro del panel, así
 * el modal (portaleado aparte) maneja los suyos sin que el panel se cierre
 * ni le robe el foco. */
export function BrandDrawer({
  isOpen,
  onClose,
  title,
  eyebrow,
  subtitle,
  footer,
  children,
  closeLabel = "Cerrar panel",
}: BrandDrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const previousActive = useRef<HTMLElement | null>(null);
  const titleId = useId();
  const mounted = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );

  useEffect(() => {
    if (!isOpen) return;
    previousActive.current = document.activeElement as HTMLElement | null;
    const timer = window.setTimeout(() => closeRef.current?.focus(), 30);
    return () => {
      window.clearTimeout(timer);
      const target = previousActive.current;
      if (target?.isConnected) target.focus();
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      const root = drawerRef.current;
      if (!root) return;
      const active = document.activeElement;
      const inside = root.contains(active) || active === document.body;
      if (!inside) return;
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
        return;
      }
      if (e.key !== "Tab") return;
      const items = focusables(root);
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (e.shiftKey && (active === first || !root.contains(active))) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && (active === last || !root.contains(active))) {
        e.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !mounted) return null;

  return createPortal(
    <>
      <div
        className="fixed inset-0 z-[90] bg-[rgba(20,20,20,.35)]"
        aria-hidden="true"
        onClick={onClose}
      />
      <div
        ref={drawerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="fixed inset-y-0 right-0 z-[91] flex w-[min(480px,100vw)] flex-col border-l border-border bg-card pt-[env(safe-area-inset-top,0px)] shadow-[-12px_0_40px_rgba(0,0,0,.14)] dark:shadow-[-12px_0_40px_rgba(0,0,0,.5)]"
      >
        <div className="flex items-start justify-between gap-3 border-b border-border px-6 pt-[22px] pb-4">
          <div className="min-w-0">
            {eyebrow}
            <h2
              id={titleId}
              className="mt-2 flex items-center gap-1.5 font-heading text-lg font-extrabold leading-[1.3] tabular-nums text-foreground"
            >
              {title}
            </h2>
            {subtitle && (
              <p className="mt-0.5 font-body text-xs text-muted-foreground">{subtitle}</p>
            )}
          </div>
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            aria-label={closeLabel}
            className="cursor-pointer rounded-[8px] p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-2 focus-visible:outline-brand-orange"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <div className="thin-scrollbar flex-1 overflow-y-auto px-6 pt-1 pb-6">{children}</div>

        {footer && (
          <div className="flex items-center justify-between gap-3 border-t border-border px-6 pt-3.5 pb-[calc(14px+env(safe-area-inset-bottom,0px))]">
            {footer}
          </div>
        )}
      </div>
    </>,
    document.body,
  );
}
