"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { authApi } from "@/features/auth/api/auth-api";
import { ApiError } from "@/services/http-client";

export function useLogin() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function login(email: string, password: string): Promise<void> {
    setLoading(true);
    try {
      await authApi.login({ email, password });
      toast.success("Bienvenido");
      router.push("/");
      router.refresh();
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Error de red";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }

  return { login, loading };
}
