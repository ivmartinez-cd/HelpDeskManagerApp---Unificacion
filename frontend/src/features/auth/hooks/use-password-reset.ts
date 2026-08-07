"use client";

import { useState } from "react";
import { toast } from "sonner";
import { authApi } from "@/features/auth/api/auth-api";
import { ApiError } from "@/services/http-client";

export type ResetPasswordResult = { ok: true } | { ok: false; code: string; message: string };

/** `forgotPassword` y `resetPassword` de las pantallas públicas
 * /forgot-password y /reset-password (Etapa 13.5). Separado de use-login.ts
 * porque ninguno de los dos flujos termina en una sesión activa. */
export function usePasswordReset() {
  const [forgotLoading, setForgotLoading] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);

  async function forgotPassword(email: string): Promise<string | null> {
    setForgotLoading(true);
    try {
      const { message } = await authApi.forgotPassword(email);
      return message;
    } catch (error) {
      // El backend responde 202 tanto si el email existe como si no — solo
      // llegamos acá por un error real (red caída, 422 de formato), no por
      // "usuario inexistente". Ahí sí corresponde avisar, no fingir éxito.
      const message = error instanceof ApiError ? error.message : "Error de red";
      toast.error(message);
      return null;
    } finally {
      setForgotLoading(false);
    }
  }

  async function resetPassword(token: string, newPassword: string): Promise<ResetPasswordResult> {
    setResetLoading(true);
    try {
      await authApi.resetPassword(token, newPassword);
      return { ok: true };
    } catch (error) {
      if (error instanceof ApiError) {
        return { ok: false, code: error.code, message: error.message };
      }
      return { ok: false, code: "NETWORK_ERROR", message: "Error de red" };
    } finally {
      setResetLoading(false);
    }
  }

  return { forgotPassword, forgotLoading, resetPassword, resetLoading };
}
