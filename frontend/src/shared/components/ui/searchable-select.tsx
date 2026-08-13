"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Check, ChevronDown, Plus, X } from "lucide-react";
import { cn } from "@/shared/utils/cn";

/** Combobox con búsqueda del design system de marca (mismos tokens
 * dark-aware que `brand-form.tsx`). Single o multi según `multiple`;
 * `allowCustom` habilita agregar valores fuera del catálogo (para campos
 * cuyo backend acepta texto libre, ej. clientes de Gestión en Coberturas). */

export interface SearchableSelectOption {
  id: string;
  label: string;
  sublabel?: string;
  color?: string | null;
}

interface CommonProps {
  label: string;
  options: SearchableSelectOption[];
  placeholder?: string;
  error?: string;
  /** Ids a ocultar del listado (ej. evitar elegir al ausente como reemplazante) */
  exclude?: string[];
  disabled?: boolean;
  allowCustom?: boolean;
}

type SearchableSelectProps = CommonProps &
  (
    | { multiple?: false; value: string | null; onChange: (value: string | null) => void }
    | { multiple: true; value: string[]; onChange: (value: string[]) => void }
  );

function OptionIdentity({ option }: { option: SearchableSelectOption }) {
  return (
    <span className="flex min-w-0 items-center gap-2">
      {option.color !== undefined && (
        <span
          aria-hidden="true"
          className="h-2.5 w-2.5 flex-none rounded-[3px]"
          style={{ backgroundColor: option.color ?? "var(--muted-foreground)" }}
        />
      )}
      <span className="truncate font-body text-sm text-foreground">{option.label}</span>
      {option.sublabel && (
        <span className="truncate font-body text-xs text-muted-foreground">
          {option.sublabel}
        </span>
      )}
    </span>
  );
}

export function SearchableSelect(props: SearchableSelectProps) {
  const { label, options, placeholder = "Buscá…", error, exclude, disabled, allowCustom } = props;
  const selectedIds = useMemo(
    () => (props.multiple ? props.value : props.value ? [props.value] : []),
    [props.multiple, props.value],
  );
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const rootRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const baseId = useId();
  const listboxId = `${baseId}-listbox`;
  const errorId = `${baseId}-error`;

  const visibles = useMemo(() => {
    const q = query.trim().toLowerCase();
    const noExcluidas = options.filter((o) => !(exclude ?? []).includes(o.id));
    const filtradas = q
      ? noExcluidas.filter((o) =>
          [o.label, o.sublabel ?? "", o.id].some((t) => t.toLowerCase().includes(q)),
        )
      : noExcluidas;
    const custom =
      allowCustom && q && !filtradas.some((o) => o.label.toLowerCase() === q)
        ? [{ id: query.trim(), label: query.trim(), sublabel: "agregar" }]
        : [];
    return [...filtradas, ...custom];
  }, [options, exclude, query, allowCustom]);

  useEffect(() => {
    if (!open) return;
    searchRef.current?.focus();
    const onOutside = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onOutside);
    return () => document.removeEventListener("mousedown", onOutside);
  }, [open]);

  // El índice activo no puede quedar apuntando fuera del listado filtrado.
  const active = Math.min(activeIndex, Math.max(visibles.length - 1, 0));

  const pick = (id: string) => {
    if (props.multiple) {
      const next = selectedIds.includes(id)
        ? selectedIds.filter((v) => v !== id)
        : [...selectedIds, id];
      props.onChange(next);
      setQuery("");
    } else {
      props.onChange(id === props.value ? null : id);
      setOpen(false);
      setQuery("");
    }
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex(Math.min(active + 1, visibles.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex(Math.max(active - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (visibles[active]) pick(visibles[active].id);
    } else if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
    }
  };

  const labelOf = (id: string) => options.find((o) => o.id === id)?.label ?? id;
  const singleSelected = !props.multiple && props.value ? options.find((o) => o.id === props.value) : null;

  return (
    <div ref={rootRef} className="relative flex flex-col gap-1.5">
      <span
        id={`${baseId}-label`}
        className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground"
      >
        {label}
      </span>
      <button
        type="button"
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-controls={listboxId}
        aria-labelledby={`${baseId}-label`}
        aria-describedby={error ? errorId : undefined}
        disabled={disabled}
        onClick={() => setOpen((v) => !v)}
        onKeyDown={(e) => {
          if (!open && (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            setOpen(true);
          }
        }}
        className={cn(
          "flex min-h-[40px] w-full items-center justify-between gap-2 rounded-[8px] border bg-card px-[14px] py-[7px] text-left outline-none focus:ring-2 focus:ring-brand-orange/40 disabled:cursor-not-allowed disabled:opacity-60",
          error ? "border-destructive" : "border-border",
        )}
      >
        {props.multiple ? (
          selectedIds.length === 0 ? (
            <span className="font-body text-sm text-muted-foreground">{placeholder}</span>
          ) : (
            <span className="flex flex-wrap items-center gap-1.5">
              {selectedIds.map((id) => (
                <span
                  key={id}
                  className="inline-flex items-center gap-1 rounded-full bg-brand-orange/10 px-2 py-0.5 font-body text-xs font-semibold text-brand-orange"
                >
                  {labelOf(id)}
                  <span
                    role="button"
                    tabIndex={0}
                    aria-label={`Quitar ${labelOf(id)}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      pick(id);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        e.stopPropagation();
                        pick(id);
                      }
                    }}
                    className="rounded-full p-0.5 hover:bg-brand-orange/20"
                  >
                    <X className="h-3 w-3" />
                  </span>
                </span>
              ))}
            </span>
          )
        ) : singleSelected ? (
          <OptionIdentity option={singleSelected} />
        ) : props.value ? (
          <span className="font-body text-sm text-foreground">{props.value}</span>
        ) : (
          <span className="font-body text-sm text-muted-foreground">{placeholder}</span>
        )}
        <ChevronDown
          className={cn("h-4 w-4 flex-none text-muted-foreground transition-transform", open && "rotate-180")}
        />
      </button>

      {open && (
        <div className="absolute top-full z-50 mt-1.5 w-full rounded-[10px] border border-border bg-card p-1.5 shadow-lg">
          <input
            ref={searchRef}
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActiveIndex(0);
            }}
            onKeyDown={onKeyDown}
            placeholder={placeholder}
            aria-label={`Buscar en ${label}`}
            aria-activedescendant={visibles[active] ? `${baseId}-opt-${active}` : undefined}
            className="mb-1 w-full rounded-[6px] border border-border bg-background px-3 py-2 font-body text-sm text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40"
          />
          <ul id={listboxId} role="listbox" aria-multiselectable={props.multiple || undefined} className="max-h-56 overflow-y-auto thin-scrollbar">
            {visibles.length === 0 && (
              <li className="px-3 py-2.5 font-body text-sm text-muted-foreground">Sin resultados</li>
            )}
            {visibles.map((o, i) => {
              const isSelected = selectedIds.includes(o.id);
              const isCustom = o.sublabel === "agregar";
              return (
                <li
                  key={o.id}
                  id={`${baseId}-opt-${i}`}
                  role="option"
                  aria-selected={isSelected}
                  onMouseEnter={() => setActiveIndex(i)}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    pick(o.id);
                  }}
                  className={cn(
                    "flex cursor-pointer items-center justify-between gap-2 rounded-[6px] px-3 py-2",
                    i === active && "bg-muted",
                  )}
                >
                  {isCustom ? (
                    <span className="flex items-center gap-2 font-body text-sm text-brand-orange">
                      <Plus className="h-3.5 w-3.5" /> Agregar «{o.label}»
                    </span>
                  ) : (
                    <OptionIdentity option={o} />
                  )}
                  {isSelected && <Check className="h-4 w-4 flex-none text-brand-orange" />}
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {error && (
        <p role="alert" id={errorId} className="font-body text-xs text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
