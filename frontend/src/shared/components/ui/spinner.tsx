import { LoaderCircle } from "lucide-react";
import { cn } from "@/shared/utils/cn";

interface SpinnerProps {
  className?: string;
  label?: string;
}

export function Spinner({ className, label = "Cargando" }: SpinnerProps) {
  return (
    <span role="status" className="inline-flex items-center justify-center">
      <LoaderCircle className={cn("h-6 w-6 animate-spin text-accent", className)} />
      <span className="sr-only">{label}</span>
    </span>
  );
}
