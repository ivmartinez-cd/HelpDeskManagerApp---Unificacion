"use client";

import { useState } from "react";
import { toast } from "sonner";
import { authApi } from "@/features/auth/api/auth-api";
import { ApiError } from "@/services/http-client";

export type ChangePasswordResult = { ok: true } | { ok: false; message: string };

/** Cambio de contraseña desde adentro de la app (modal en el header del
 * shell). A diferencia de /reset-password, acá el usuario ya está logueado
 * y el backend conserva su sesión actual — solo revoca las demás
 * (change_password.py). */
export function useChangePassword() {
  const [loading, setLoading] = useState(false);

  async function changePassword(
    currentPassword: string,
    newPassword: string,
  ): Promise<ChangePasswordResult> {
    setLoading(true);
    try {
      await authApi.changePassword(currentPassword, newPassword);
      toast.success("Contraseña actualizada. Se cerraron tus sesiones en otros dispositivos.");
      return { ok: true };
    } catch (error) {
      if (error instanceof ApiError && error.code === "INVALID_CREDENTIALS") {
        // El backend usa el mismo INVALID_CREDENTIALS genérico que el login
        // (anti-enumeración ahí tiene sentido); acá el usuario ya está
        // identificado y sabemos que el campo que falló es "la actual".
        return { ok: false, message: "La contraseña actual no es correcta" };
      }
      const message = error instanceof ApiError ? error.message : "Error de red";
      return { ok: false, message };
    } finally {
      setLoading(false);
    }
  }

  return { changePassword, loading };
}
