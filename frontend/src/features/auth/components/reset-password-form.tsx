"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Eye, EyeOff, Loader2, ShieldAlert } from "lucide-react";
import { AuthSplitLayout } from "@/features/auth/components/auth-split-layout";
import { PasswordRequirements } from "@/features/auth/components/password-requirements";
import { usePasswordReset } from "@/features/auth/hooks/use-password-reset";

interface ResetPasswordFormProps {
  token: string | null;
  isActivation: boolean;
}

// Mismos tokens literales que login-form.tsx (no dark-aware: AuthSplitLayout
// fuerza fondo claro sea cual sea el tema de la app, y `defaultTheme="dark"`
// hace que un usuario nuevo activando su cuenta por primera vez SIEMPRE
// llegue acá con el tema oscuro puesto — texto casi invisible si se usan
// tokens tipo `text-foreground`/`bg-background`).
const fieldLabelClass = "font-body text-[13px] font-semibold text-[#4b4b4b]";
const fieldInputClass =
  "w-full rounded-[8px] border border-black/15 bg-white px-[14px] py-[11px] font-body text-sm text-brand-charcoal outline-none transition-shadow focus:ring-2 focus:ring-brand-orange/40";

interface TerminalError {
  title: string;
  message: string;
  action: { href: string; label: string };
}

// Los 3 códigos que el backend puede devolver para un token ya inválido en
// sí mismo (a diferencia de WEAK_PASSWORD, que es sobre el password nuevo y
// no invalida el token — ver ResetPassword en el backend).
const TERMINAL_ERRORS: Record<string, TerminalError> = {
  TOKEN_INVALID: {
    title: "Este link no es válido",
    message: "Pedí uno nuevo para continuar.",
    action: { href: "/forgot-password", label: "Pedir un link nuevo" },
  },
  TOKEN_EXPIRED: {
    title: "Este link venció",
    message: "Los links duran 30 minutos. Pedí uno nuevo para continuar.",
    action: { href: "/forgot-password", label: "Pedir un link nuevo" },
  },
  TOKEN_ALREADY_USED: {
    title: "Este link ya se usó",
    message: "Si fuiste vos quien lo usó, iniciá sesión con tu nueva contraseña.",
    action: { href: "/login", label: "Ir a iniciar sesión" },
  },
};

export function ResetPasswordForm({ token, isActivation }: ResetPasswordFormProps) {
  const router = useRouter();
  const { resetPassword, resetLoading } = usePasswordReset();
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [terminalError, setTerminalError] = useState<TerminalError | null>(
    token ? null : TERMINAL_ERRORS.TOKEN_INVALID,
  );

  async function handleSubmit(event: FormEvent): Promise<void> {
    event.preventDefault();
    setFieldError(null);
    if (newPassword !== confirmPassword) {
      setFieldError("Las contraseñas no coinciden");
      return;
    }
    if (!token) return;

    const result = await resetPassword(token, newPassword);
    if (result.ok) {
      toast.success(
        isActivation ? "Cuenta activada. Ya podés iniciar sesión." : "Contraseña actualizada.",
      );
      router.push("/login");
      return;
    }
    if (result.code in TERMINAL_ERRORS) {
      setTerminalError(TERMINAL_ERRORS[result.code]);
      return;
    }
    // WEAK_PASSWORD y cualquier otro (red, etc.) se muestran inline, junto
    // al campo — el token sigue siendo válido, no hace falta pedir otro.
    setFieldError(result.message);
  }

  if (terminalError) {
    return (
      <AuthSplitLayout>
        <div className="flex flex-col items-center text-center">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-red-500/10 text-red-600">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <h2 className="font-heading text-2xl font-extrabold text-brand-charcoal">
            {terminalError.title}
          </h2>
          <p className="mt-2 font-body text-sm text-[#8a8a8a]">{terminalError.message}</p>
          <Link
            href={terminalError.action.href}
            className="mt-8 font-body text-sm font-semibold text-brand-orange no-underline hover:text-brand-orange-hover"
          >
            {terminalError.action.label}
          </Link>
        </div>
      </AuthSplitLayout>
    );
  }

  return (
    <AuthSplitLayout>
      <div className="mb-[26px] flex flex-col gap-1.5">
        <h2 className="font-heading text-[25px] font-extrabold text-brand-charcoal">
          {isActivation ? "Activá tu cuenta" : "Elegí una nueva contraseña"}
        </h2>
        <p className="font-body text-sm text-[#8a8a8a]">
          {isActivation
            ? "Definí tu contraseña para empezar a usar la plataforma"
            : "Ingresá tu nueva contraseña para recuperar el acceso"}
        </p>
      </div>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <label htmlFor="new-password" className={fieldLabelClass}>
            Nueva contraseña
          </label>
          <div className="relative">
            <input
              id="new-password"
              type={showPassword ? "text" : "password"}
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              placeholder="••••••••"
              autoComplete="new-password"
              required
              className={`${fieldInputClass} pr-10`}
            />
            <button
              type="button"
              onClick={() => setShowPassword((visible) => !visible)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[#8a8a8a] hover:text-brand-charcoal"
              aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          <div className="mt-2">
            <PasswordRequirements password={newPassword} surface="brand" />
          </div>
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="confirm-password" className={fieldLabelClass}>
            Confirmar contraseña
          </label>
          <input
            id="confirm-password"
            type={showPassword ? "text" : "password"}
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            placeholder="••••••••"
            autoComplete="new-password"
            required
            className={fieldInputClass}
          />
        </div>
        {fieldError && <p className="font-body text-xs text-red-600">{fieldError}</p>}
        <button
          type="submit"
          disabled={resetLoading}
          className="mt-1.5 flex items-center justify-center gap-2 rounded-[8px] bg-brand-orange px-[18px] py-3 font-body text-sm font-bold text-white transition-colors hover:bg-brand-orange-hover disabled:opacity-50"
        >
          {resetLoading && <Loader2 className="h-4 w-4 animate-spin" />}
          {isActivation ? "Activar cuenta" : "Restablecer contraseña"}
        </button>
      </form>
    </AuthSplitLayout>
  );
}
