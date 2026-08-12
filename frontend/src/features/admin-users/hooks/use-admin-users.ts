"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { adminUsersApi, type AdminUser } from "@/features/admin-users/api/admin-users-api";
import { ApiError } from "@/services/http-client";

const PAGE_SIZE = 20;

function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Error de red";
}

export function useAdminUsers() {
  const [items, setItems] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const result = await adminUsersApi.list({ page, size: PAGE_SIZE, q: query || undefined });
      setItems(result.items);
      setTotal(result.total);
    } catch (error) {
      toast.error(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [page, query]);

  useEffect(() => {
    // fetch-on-mount/on-page-or-query-change; `reload` flips `loading`
    // synchronously on purpose so the table doesn't render stale rows.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void reload();
  }, [reload]);

  function search(q: string): void {
    setQuery(q);
    setPage(1);
  }

  async function createUser(email: string, fullName: string): Promise<boolean> {
    try {
      await adminUsersApi.create({ email, fullName });
      toast.success("Usuario creado. Se envió un link de activación.");
      await reload();
      return true;
    } catch (error) {
      toast.error(errorMessage(error));
      return false;
    }
  }

  async function toggleActive(user: AdminUser): Promise<void> {
    try {
      await adminUsersApi.update(user.id, { isActive: !user.isActive });
      toast.success(user.isActive ? "Usuario desactivado" : "Usuario activado");
      await reload();
    } catch (error) {
      toast.error(errorMessage(error));
    }
  }

  async function updateColor(user: AdminUser, color: string): Promise<boolean> {
    try {
      await adminUsersApi.update(user.id, { color });
      toast.success("Color actualizado");
      await reload();
      return true;
    } catch (error) {
      toast.error(errorMessage(error));
      return false;
    }
  }

  async function triggerPasswordReset(user: AdminUser): Promise<void> {
    try {
      await adminUsersApi.triggerPasswordReset(user.id);
      toast.success(`Se envió un link de restablecimiento a ${user.email}`);
    } catch (error) {
      toast.error(errorMessage(error));
    }
  }

  return {
    items,
    total,
    page,
    setPage,
    query,
    search,
    loading,
    pageSize: PAGE_SIZE,
    createUser,
    toggleActive,
    updateColor,
    triggerPasswordReset,
  };
}
