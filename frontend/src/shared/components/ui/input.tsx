import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/shared/utils/cn";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, id, ...props }, ref) => (
    <div className="space-y-1.5">
      {label && (
        <label
          htmlFor={id}
          className="text-xs font-bold uppercase tracking-wide text-muted-foreground"
        >
          {label}
        </label>
      )}
      <input
        ref={ref}
        id={id}
        className={cn(
          "w-full rounded-xl border border-black/10 dark:border-white/10 bg-background px-3 py-2 text-sm outline-none transition-colors focus:ring-2 focus:ring-accent/40",
          error && "border-destructive",
          className,
        )}
        {...props}
      />
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  ),
);
Input.displayName = "Input";
