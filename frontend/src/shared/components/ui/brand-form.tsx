import {
  useId,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
} from "react";
import { Loader2, type LucideIcon } from "lucide-react";
import { cn } from "@/shared/utils/cn";

/** Primitivos de formulario con la identidad visual de marca (radios,
 * tipografía y tokens propios de Canal Directo) para usar dentro de
 * `BrandModal` o el hub de Contadores. A diferencia de
 * `shared/components/ui/{input,file-input,button,card,stat-card,
 * empty-state}.tsx`, usan tokens dark-aware (`bg-card`, `text-foreground`,
 * `text-muted-foreground`) igual que el resto del design system — hasta
 * 2026-08-11 eran literales y siempre claros (el bug que motivó este
 * archivo: el resto de la app corre en tema oscuro por default, y los
 * componentes genéricos de entonces renderizaban cajas negras dentro de un
 * modal blanco de marca). El acento naranja/gris institucional
 * (`bg-brand-orange`, etc.) sigue fijo a propósito: es color de marca, no
 * de tema. */

const brandFieldLabelClass =
  "font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground";

interface BrandInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  hint?: string;
}

export function BrandInput({ label, hint, id, className, ...props }: BrandInputProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className={brandFieldLabelClass}>
        {label}
      </label>
      <input
        id={inputId}
        {...props}
        className={cn(
          "rounded-[8px] border border-border bg-card px-[14px] py-[9px] font-body text-sm text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40",
          className,
        )}
      />
      {hint && <p className="font-body text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

interface BrandSelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  hint?: string;
}

export function BrandSelect({ label, hint, id, className, children, ...props }: BrandSelectProps) {
  const generatedId = useId();
  const selectId = id ?? generatedId;
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={selectId} className={brandFieldLabelClass}>
        {label}
      </label>
      <select
        id={selectId}
        {...props}
        className={cn(
          "rounded-[8px] border border-border bg-card px-[14px] py-[9px] font-body text-sm text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40",
          className,
        )}
      >
        {children}
      </select>
      {hint && <p className="font-body text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

interface BrandFileInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label: string;
  hint?: string;
}

export function BrandFileInput({ label, hint, id, className, ...props }: BrandFileInputProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className={brandFieldLabelClass}>
        {label}
      </label>
      <input
        id={inputId}
        type="file"
        {...props}
        className={cn(
          "w-full rounded-[8px] border border-border bg-card px-3 py-2 font-body text-sm text-foreground outline-none file:mr-3 file:rounded-[6px] file:border-0 file:bg-brand-orange/10 file:px-3 file:py-1.5 file:font-body file:text-xs file:font-bold file:uppercase file:tracking-wide file:text-brand-orange hover:file:bg-brand-orange/20 focus:ring-2 focus:ring-brand-orange/40",
          className,
        )}
      />
      {hint && <p className="font-body text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}

interface BrandButtonClassesOptions {
  variant?: "primary" | "outline";
  size?: "sm" | "md";
  className?: string;
}

export function brandButtonClasses({
  variant = "primary",
  size = "md",
  className,
}: BrandButtonClassesOptions = {}) {
  const base =
    "inline-flex cursor-pointer items-center justify-center gap-2 rounded-[10px] font-body font-bold transition-colors disabled:opacity-50 disabled:pointer-events-none";
  const variants = {
    primary: "bg-brand-orange text-white hover:bg-brand-orange-hover",
    outline: "border border-border text-foreground hover:bg-muted",
  };
  const sizes = { sm: "px-3 py-1.5 text-xs", md: "px-5 py-2.5 text-sm" };
  return cn(base, variants[variant], sizes[size], className);
}

interface BrandButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "outline";
  size?: "sm" | "md";
  loading?: boolean;
}

export function BrandButton({
  variant = "primary",
  size = "md",
  loading,
  className,
  children,
  disabled,
  ...props
}: BrandButtonProps) {
  return (
    <button
      className={brandButtonClasses({ variant, size, className })}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" />}
      {children}
    </button>
  );
}

interface BrandStatTileProps {
  label: string;
  value: string | number;
  hint?: string;
  tone?: "neutral" | "highlight";
}

export function BrandStatTile({ label, value, hint, tone = "neutral" }: BrandStatTileProps) {
  const toneClass =
    tone === "highlight"
      ? "border-brand-orange/20 bg-brand-orange/5 text-brand-orange"
      : "border-border bg-muted text-foreground";
  return (
    <div className={cn("rounded-[10px] border p-4", toneClass)}>
      <p className="font-body text-[11px] font-bold uppercase tracking-wide opacity-70">
        {label}
      </p>
      <p className="mt-1.5 font-heading text-2xl font-extrabold">{value}</p>
      {hint && <p className="mt-1 font-body text-xs opacity-60">{hint}</p>}
    </div>
  );
}

interface BrandEmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
}

export function BrandEmptyState({ icon: Icon, title, description }: BrandEmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-[10px] border border-dashed border-border p-10 text-center">
      <Icon className="h-8 w-8 text-muted-foreground/40" />
      <p className="font-body text-sm font-bold text-foreground">{title}</p>
      {description && <p className="font-body text-sm text-muted-foreground">{description}</p>}
    </div>
  );
}

export function BrandSkeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-[8px] bg-muted", className)} />;
}

interface BrandBadgeProps {
  variant?: "neutral" | "accent" | "success" | "danger";
  children: ReactNode;
}

const brandBadgeVariants: Record<NonNullable<BrandBadgeProps["variant"]>, string> = {
  neutral: "bg-muted text-foreground",
  accent: "bg-brand-orange/10 text-brand-orange",
  success: "bg-success/10 text-success",
  danger: "bg-destructive/10 text-destructive",
};

export function BrandBadge({ variant = "neutral", children }: BrandBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1 font-body text-[10px] font-bold uppercase tracking-wide",
        brandBadgeVariants[variant],
      )}
    >
      {children}
    </span>
  );
}

interface BrandResultPanelProps {
  title: string;
  children: ReactNode;
  className?: string;
}

export function BrandResultPanel({ title, children, className }: BrandResultPanelProps) {
  return (
    <div className={cn("rounded-[12px] border border-border bg-muted/50 p-5", className)}>
      <h3 className="mb-4 font-heading text-sm font-bold uppercase tracking-wide text-foreground">
        {title}
      </h3>
      {children}
    </div>
  );
}
