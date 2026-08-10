import { Check, X } from "lucide-react";
import { cn } from "@/shared/utils/cn";

interface PasswordRequirementsProps {
  password: string;
  /** Este checklist vive en dos contextos con fondo distinto: dentro de
   * `AuthSplitLayout` (fondo siempre claro — `bg-brand-surface` — sea cual
   * sea el tema de la app, ver login/forgot-password/reset-password) o
   * dentro del `Modal` genérico (fondo que sí sigue el tema, ver
   * change-password-modal.tsx). Usar tokens dark-aware (`text-foreground`)
   * en el primer caso lo volvía invisible con el tema oscuro por defecto
   * (`defaultTheme="dark"`) — texto casi blanco sobre fondo claro forzado.
   * "brand" = colores literales de marca; "themed" (default) = tokens que
   * siguen el tema, para no romper el uso dentro del Modal genérico. */
  surface?: "brand" | "themed";
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

export function PasswordRequirements({ password, surface = "themed" }: PasswordRequirementsProps) {
  const metClass = surface === "brand" ? "text-brand-charcoal" : "text-foreground";
  const unmetClass = surface === "brand" ? "text-[#9a9a9a]" : "text-muted-foreground";
  const checkClass = surface === "brand" ? "text-brand-orange" : "text-accent";

  return (
    <ul className={cn("space-y-1 text-xs", surface === "brand" && "font-body")}>
      {RULES.map((rule) => {
        const met = rule.test(password);
        return (
          <li
            key={rule.label}
            className={cn("flex items-center gap-2", met ? metClass : unmetClass)}
          >
            {met ? (
              <Check className={cn("h-3.5 w-3.5 shrink-0", checkClass)} />
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
