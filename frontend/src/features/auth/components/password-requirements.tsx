import { Check, X } from "lucide-react";
import { cn } from "@/shared/utils/cn";

interface PasswordRequirementsProps {
  password: string;
}

// Espejo de los 4 checks de `RawPassword.__post_init__`
// (backend/src/modules/auth/domain/value_objects/raw_password.py) — el
// backend sigue siendo la única autoridad, esto es feedback en vivo. Si se
// endurece la política ahí (ver riesgo #3 del plan de auth), actualizar acá.
const RULES: { label: string; test: (value: string) => boolean }[] = [
  { label: "Al menos 8 caracteres", test: (value) => value.length >= 8 },
  { label: "Una letra mayúscula", test: (value) => /[A-Z]/.test(value) },
  { label: "Un número", test: (value) => /[0-9]/.test(value) },
  { label: "Un carácter especial", test: (value) => /[^A-Za-z0-9]/.test(value) },
];

export function PasswordRequirements({ password }: PasswordRequirementsProps) {
  return (
    <ul className="space-y-1 text-xs">
      {RULES.map((rule) => {
        const met = rule.test(password);
        return (
          <li
            key={rule.label}
            className={cn(
              "flex items-center gap-2",
              met ? "text-foreground" : "text-muted-foreground",
            )}
          >
            {met ? (
              <Check className="h-3.5 w-3.5 shrink-0 text-accent" />
            ) : (
              <X className="h-3.5 w-3.5 shrink-0 opacity-40" />
            )}
            {rule.label}
          </li>
        );
      })}
    </ul>
  );
}
