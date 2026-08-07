"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { MailCheck } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { AuthSplitLayout } from "@/features/auth/components/auth-split-layout";
import { usePasswordReset } from "@/features/auth/hooks/use-password-reset";

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
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10 text-accent">
            <MailCheck className="h-6 w-6" />
          </div>
          <h2 className="text-2xl font-bold text-foreground">Revisá tu email</h2>
          <p className="mt-2 text-sm text-muted-foreground">{confirmation}</p>
          <Link href="/login" className="mt-8 text-sm font-medium text-accent hover:underline">
            Volver a iniciar sesión
          </Link>
        </div>
      </AuthSplitLayout>
    );
  }

  return (
    <AuthSplitLayout>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-foreground">¿Olvidaste tu contraseña?</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Ingresá tu email y te mandamos un link para restablecerla
        </p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          id="email"
          label="Email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="tu.nombre@empresa.com"
          autoComplete="username"
          required
        />
        <Button type="submit" loading={forgotLoading} className="w-full">
          Enviar instrucciones
        </Button>
      </form>
      <p className="mt-6 text-center text-sm">
        <Link href="/login" className="font-medium text-accent hover:underline">
          Volver a iniciar sesión
        </Link>
      </p>
    </AuthSplitLayout>
  );
}
