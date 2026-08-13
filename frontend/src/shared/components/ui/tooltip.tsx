"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { cn } from "@/shared/utils/cn";

/** Tooltip con delay configurable (API del handoff de reasignación
 * temporal). Renderiza el contenido en un portal con `position: fixed`
 * porque los triggers típicos (pills del Calendario) viven dentro de
 * contenedores con overflow que recortarían un `absolute`. El contenido es
 * hovereable (para links tipo "Ver detalle →"); Escape lo cierra. */

interface TooltipProps {
  content: React.ReactNode;
  /** ms antes de mostrar; default 200 */
  delay?: number;
  placement?: "top" | "bottom" | "left" | "right";
  children: React.ReactNode;
  /** Clase del wrapper del trigger (es un div, block por default). */
  className?: string;
}

type Position = { top: number; left: number };

const PLACEMENT_TRANSFORM: Record<NonNullable<TooltipProps["placement"]>, string> = {
  top: "translate(-50%, -100%)",
  bottom: "translate(-50%, 0)",
  left: "translate(-100%, -50%)",
  right: "translate(0, -50%)",
};

function positionFor(rect: DOMRect, placement: NonNullable<TooltipProps["placement"]>): Position {
  const gap = 8;
  switch (placement) {
    case "top":
      return { top: rect.top - gap, left: rect.left + rect.width / 2 };
    case "bottom":
      return { top: rect.bottom + gap, left: rect.left + rect.width / 2 };
    case "left":
      return { top: rect.top + rect.height / 2, left: rect.left - gap };
    case "right":
      return { top: rect.top + rect.height / 2, left: rect.right + gap };
  }
}

export function Tooltip({
  content,
  delay = 200,
  placement = "top",
  children,
  className,
}: TooltipProps) {
  const id = useId();
  const triggerRef = useRef<HTMLDivElement>(null);
  const showTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [position, setPosition] = useState<Position | null>(null);

  const cancelTimers = useCallback(() => {
    if (showTimer.current) clearTimeout(showTimer.current);
    if (hideTimer.current) clearTimeout(hideTimer.current);
  }, []);

  const show = useCallback(() => {
    cancelTimers();
    showTimer.current = setTimeout(() => {
      const rect = triggerRef.current?.getBoundingClientRect();
      if (rect) setPosition(positionFor(rect, placement));
    }, delay);
  }, [cancelTimers, delay, placement]);

  const hide = useCallback(() => {
    cancelTimers();
    // Pequeña gracia para poder entrar con el mouse al contenido del tooltip.
    hideTimer.current = setTimeout(() => setPosition(null), 120);
  }, [cancelTimers]);

  useEffect(() => {
    if (!position) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setPosition(null);
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [position]);

  useEffect(() => cancelTimers, [cancelTimers]);

  return (
    <div
      ref={triggerRef}
      className={className}
      aria-describedby={position ? id : undefined}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {children}
      {position &&
        createPortal(
          <div
            role="tooltip"
            id={id}
            style={{ top: position.top, left: position.left, transform: PLACEMENT_TRANSFORM[placement] }}
            className={cn(
              "fixed z-50 min-w-[240px] rounded-[12px] border border-border bg-card px-4 py-3 shadow-lg",
            )}
            onMouseEnter={cancelTimers}
            onMouseLeave={hide}
          >
            {content}
          </div>,
          document.body,
        )}
    </div>
  );
}
