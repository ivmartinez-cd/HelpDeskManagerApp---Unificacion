"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { Loader2, MailCheck } from "lucide-react";
import { AuthSplitLayout } from "@/features/auth/components/auth-split-layout";
import { usePasswordReset } from "@/features/auth/hooks/use-password-reset";

// Mismos tokens literales que login-form.tsx — ver el comentario equivalente
// en reset-password-form.tsx (AuthSplitLayout fuerza fondo claro, tokens
// dark-aware como `text-foreground` se vuelven invisibles con el tema
// oscuro por defecto).
const fieldLabelClass = "font-body text-[13px] font-semibold text-[#4b4b4b]";
const fieldInputClass =
  "w-full rounded-[8px] border border-black/15 bg-white px-[14px] py-[11px] font-body text-sm text-brand-charcoal outline-none transition-shadow focus:ring-2 focus:ring-brand-orange/40";

export function ForgotPasswordForm() {
  const { forgotPassword, forgotLoading } = usePasswordReset();
  const [email, setEmail] = useState("");
  const [confirmation, setConfirmation] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent): Promise<void> {
    event.preventDefault();
    const message = await forgotPassword(email);
    // Mismo estado exista o no la cuenta — es el mismo criterio anti-
    // enumeración del backend, replicado acá (ver §3 del plan de la etapa).
    if (message) setConfirmation(message);
  }

  if (confirmation) {
    return (
      <AuthSplitLayout>
        <div className="flex flex-col items-center text-center">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-orange/10 text-brand-orange">
            <MailCheck className="h-6 w-6" />
          </div>
          <h2 className="font-heading text-2xl font-extrabold text-brand-charcoal">
            Revisá tu email
          </h2>
          <p className="mt-2 font-body text-sm text-[#8a8a8a]">{confirmation}</p>
          <Link
            href="/login"
            className="mt-8 font-body text-sm font-semibold text-brand-orange no-underline hover:text-brand-orange-hover"
          >
            Volver a iniciar sesión
          </Link>
        </div>
      </AuthSplitLayout>
    );
  }

  return (
    <AuthSplitLayout>
      <div className="mb-[26px] flex flex-col gap-1.5">
        <h2 className="font-heading text-[25px] font-extrabold text-brand-charcoal">
          ¿Olvidaste tu contraseña?
        </h2>
        <p className="font-body text-sm text-[#8a8a8a]">
          Ingresá tu email y te mandamos un link para restablecerla
        </p>
      </div>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <label htmlFor="email" className={fieldLabelClass}>
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="tu.nombre@empresa.com"
            autoComplete="username"
            required
            className={fieldInputClass}
          />
        </div>
        <button
          type="submit"
          disabled={forgotLoading}
          className="mt-1.5 flex items-center justify-center gap-2 rounded-[8px] bg-brand-orange px-[18px] py-3 font-body text-sm font-bold text-white transition-colors hover:bg-brand-orange-hover disabled:opacity-50"
        >
          {forgotLoading && <Loader2 className="h-4 w-4 animate-spin" />}
          Enviar instrucciones
        </button>
      </form>
      <p className="mt-6 text-center font-body text-sm">
        <Link
          href="/login"
          className="font-semibold text-brand-orange no-underline hover:text-brand-orange-hover"
        >
          Volver a iniciar sesión
        </Link>
      </p>
    </AuthSplitLayout>
  );
}
