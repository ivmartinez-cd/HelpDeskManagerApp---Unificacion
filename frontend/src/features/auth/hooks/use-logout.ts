"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/features/auth/api/auth-api";

export function useLogout() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function logout(): Promise<void> {
    setLoading(true);
    try {
      await authApi.logout();
    } finally {
      setLoading(false);
      router.push("/login");
      router.refresh();
    }
  }

  return { logout, loading };
}
