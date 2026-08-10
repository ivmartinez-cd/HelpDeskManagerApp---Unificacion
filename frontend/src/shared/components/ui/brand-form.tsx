import { useId, type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode } from "react";
import { Loader2, type LucideIcon } from "lucide-react";
import { cn } from "@/shared/utils/cn";

/** Primitivos de formulario para usar DENTRO de `BrandModal` (o cualquier
 * superficie clara de marca). A diferencia de `shared/components/ui/{input,
 * file-input,button,card,stat-card,empty-state}.tsx`, estos NO usan tokens
 * dark-aware (`bg-background`, `text-muted-foreground`, `dark:` variants) —
 * ese es justamente el bug que motivó este archivo: el resto de la app
 * corre en tema oscuro por default, así que esos componentes genéricos
 * renderizaban cajas negras dentro de un modal blanco de marca. Acá todo es
 * literal y siempre claro. */

const brandFieldLabelClass =
  "font-body text-[11px] font-bold uppercase tracking-wide text-[#7a7a7a]";

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
          "rounded-[8px] border border-black/[0.14] bg-white px-[14px] py-[9px] font-body text-sm text-brand-charcoal outline-none focus:ring-2 focus:ring-brand-orange/40",
          className,
        )}
      />
      {hint && <p className="font-body text-xs text-[#9a9a9a]">{hint}</p>}
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
          "w-full rounded-[8px] border border-black/[0.14] bg-white px-3 py-2 font-body text-sm text-brand-charcoal outline-none file:mr-3 file:rounded-[6px] file:border-0 file:bg-brand-orange/10 file:px-3 file:py-1.5 file:font-body file:text-xs file:font-bold file:uppercase file:tracking-wide file:text-brand-orange hover:file:bg-brand-orange/20 focus:ring-2 focus:ring-brand-orange/40",
          className,
        )}
      />
      {hint && <p className="font-body text-xs text-[#9a9a9a]">{hint}</p>}
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
    "inline-flex items-center justify-center gap-2 rounded-[10px] font-body font-bold transition-colors disabled:opacity-50 disabled:pointer-events-none";
  const variants = {
    primary: "bg-brand-orange text-white hover:bg-brand-orange-hover",
    outline: "border border-black/[0.14] text-brand-charcoal hover:bg-black/5",
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
      : "border-black/[0.08] bg-black/[0.02] text-brand-charcoal";
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
    <div className="flex flex-col items-center justify-center gap-2 rounded-[10px] border border-dashed border-black/[0.12] p-10 text-center">
      <Icon className="h-8 w-8 text-black/20" />
      <p className="font-body text-sm font-bold text-brand-charcoal">{title}</p>
      {description && <p className="font-body text-sm text-[#8a8a8a]">{description}</p>}
    </div>
  );
}

export function BrandSkeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-[8px] bg-black/[0.06]", className)} />;
}

interface BrandBadgeProps {
  variant?: "neutral" | "accent" | "success" | "danger";
  children: ReactNode;
}

const brandBadgeVariants: Record<NonNullable<BrandBadgeProps["variant"]>, string> = {
  neutral: "bg-black/[0.06] text-brand-charcoal",
  accent: "bg-brand-orange/10 text-brand-orange",
  success: "bg-[#16a34a]/10 text-[#16a34a]",
  danger: "bg-[#dc2626]/10 text-[#dc2626]",
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
    <div className={cn("rounded-[12px] border border-black/[0.08] bg-black/[0.015] p-5", className)}>
      <h3 className="mb-4 font-heading text-sm font-bold uppercase tracking-wide text-brand-charcoal">
        {title}
      </h3>
      {children}
    </div>
  );
}
