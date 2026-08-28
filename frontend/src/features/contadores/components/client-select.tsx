"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { ChevronDown } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import type { ClientOption } from "./client-picker-config";

const selectClass =
  "w-full rounded-[10px] border border-border bg-card px-[14px] py-[11px] font-body text-sm text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40 disabled:opacity-60";

type PanelPosition = { top: number; left: number; width: number };

/** Reemplaza al `<select>` nativo: el navegador decide de qué lado abre la
 * lista de opciones según el espacio disponible (y en estos modales elegía
 * hacia arriba, tapando el título), algo que no se puede forzar por CSS en
 * un `<select>` real. Este dropdown siempre despliega hacia abajo.
 *
 * El panel se porta a `document.body` con `position: fixed` (mismo motivo
 * que `tooltip.tsx`): el body de `BrandModal` tiene `overflow-y-auto` para
 * poder scrollear formularios largos, y eso recortaba la lista de opciones
 * cuando el modal no tenía más aire debajo. */
export function ClientSelect({
  value,
  onChange,
  options,
  loading,
  placeholder,
  ariaLabel,
}: {
  value: string;
  onChange: (id: string) => void;
  options: ClientOption[];
  loading: boolean;
  placeholder: string;
  ariaLabel: string;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [position, setPosition] = useState<PanelPosition | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  // Resetear búsqueda al abrir — patrón "ajustar estado durante el render"
  // (igual que confirmation-modal.tsx) para no llamar setState dentro de un
  // efecto y disparar un render adicional innecesario.
  const [prevOpen, setPrevOpen] = useState(open);
  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open) setSearch("");
  }

  useEffect(() => {
    if (!open) return;
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      if (containerRef.current?.contains(target)) return;
      if (panelRef.current?.contains(target)) return;
      setOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    // Sin el timeout el foco compite con el que BrandModal le pone al
    // primer elemento enfocable del modal al abrirse.
    const timer = setTimeout(() => searchRef.current?.focus(), 0);
    return () => clearTimeout(timer);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const updatePosition = () => {
      const rect = containerRef.current?.getBoundingClientRect();
      if (rect) setPosition({ top: rect.bottom + 4, left: rect.left, width: rect.width });
    };
    updatePosition();
    window.addEventListener("resize", updatePosition);
    // capture: true para enterarse del scroll del body de BrandModal (y de
    // cualquier otro ancestro con overflow), no solo del window.
    window.addEventListener("scroll", updatePosition, true);
    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [open]);

  const selected = options.find((o) => o.id === value);
  const filtered = options.filter((o) => o.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div
      ref={containerRef}
      className="relative w-full"
      onKeyDown={(e) => {
        if (e.key === "Escape" && open) {
          e.stopPropagation();
          setOpen(false);
        }
      }}
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        disabled={loading}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
        className={cn(selectClass, "flex items-center justify-between gap-2 text-left")}
      >
        <span className={cn("truncate", !selected && "text-muted-foreground")}>
          {loading ? "Cargando clientes..." : (selected?.name ?? placeholder)}
        </span>
        <ChevronDown
          className={cn(
            "h-4 w-4 flex-none text-muted-foreground transition-transform",
            open && "rotate-180",
          )}
        />
      </button>
      {open &&
        position &&
        createPortal(
          <div
            ref={panelRef}
            style={{ top: position.top, left: position.left, width: position.width }}
            className="fixed z-[110] flex flex-col overflow-hidden rounded-[10px] border border-border bg-card shadow-lg"
          >
            <div className="border-b border-border p-1.5">
              <input
                ref={searchRef}
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    if (filtered.length === 1) {
                      onChange(filtered[0].id);
                      setOpen(false);
                    }
                  }
                }}
                placeholder="Buscar cliente..."
                aria-label={`Buscar en ${ariaLabel}`}
                className="w-full rounded-[6px] border border-border px-2.5 py-1.5 font-body text-sm text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40"
              />
            </div>
            <ul role="listbox" aria-label={ariaLabel} className="max-h-56 overflow-y-auto thin-scrollbar py-1">
              {filtered.length === 0 ? (
                <li className="px-[14px] py-2 font-body text-sm text-muted-foreground">
                  {options.length === 0 ? "Sin clientes disponibles." : "Sin resultados."}
                </li>
              ) : (
                filtered.map((option) => (
                  <li key={option.id} role="option" aria-selected={option.id === value}>
                    <button
                      type="button"
                      onClick={() => {
                        onChange(option.id);
                        setOpen(false);
                      }}
                      className={cn(
                        "block w-full truncate px-[14px] py-2 text-left font-body text-sm",
                        option.id === value
                          ? "bg-brand-orange/10 font-semibold text-brand-orange"
                          : "text-foreground hover:bg-muted/50",
                      )}
                    >
                      {option.name}
                    </button>
                  </li>
                ))
              )}
            </ul>
          </div>,
          document.body,
        )}
    </div>
  );
}
