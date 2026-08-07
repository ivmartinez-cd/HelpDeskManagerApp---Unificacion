"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Eye, EyeOff, ShieldAlert } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { AuthSplitLayout } from "@/features/auth/components/auth-split-layout";
import { PasswordRequirements } from "@/features/auth/components/password-requirements";
import { usePasswordReset } from "@/features/auth/hooks/use-password-reset";

interface ResetPasswordFormProps {
  token: string | null;
  isActivation: boolean;
}

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
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-destructive/10 text-destructive">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <h2 className="text-2xl font-bold text-foreground">{terminalError.title}</h2>
          <p className="mt-2 text-sm text-muted-foreground">{terminalError.message}</p>
          <Link
            href={terminalError.action.href}
            className="mt-8 text-sm font-medium text-accent hover:underline"
          >
            {terminalError.action.label}
          </Link>
        </div>
      </AuthSplitLayout>
    );
  }

  return (
    <AuthSplitLayout>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-foreground">
          {isActivation ? "Activá tu cuenta" : "Elegí una nueva contraseña"}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          {isActivation
            ? "Definí tu contraseña para empezar a usar la plataforma"
            : "Ingresá tu nueva contraseña para recuperar el acceso"}
        </p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="new-password"
            className="mb-1.5 block text-xs font-bold uppercase tracking-wide text-muted-foreground"
          >
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
              className="w-full rounded-xl border border-black/10 dark:border-white/10 bg-background px-3 py-2 pr-10 text-sm outline-none focus:ring-2 focus:ring-accent/40"
            />
            <button
              type="button"
              onClick={() => setShowPassword((visible) => !visible)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          <div className="mt-2">
            <PasswordRequirements password={newPassword} />
          </div>
        </div>
        <div>
          <label
            htmlFor="confirm-password"
            className="mb-1.5 block text-xs font-bold uppercase tracking-wide text-muted-foreground"
          >
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
            className="w-full rounded-xl border border-black/10 dark:border-white/10 bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-accent/40"
          />
        </div>
        {fieldError && <p className="text-xs text-destructive">{fieldError}</p>}
        <Button type="submit" loading={resetLoading} className="w-full">
          {isActivation ? "Activar cuenta" : "Restablecer contraseña"}
        </Button>
      </form>
    </AuthSplitLayout>
  );
}
