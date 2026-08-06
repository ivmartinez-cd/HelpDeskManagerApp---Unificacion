"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import {
  adminPermissionsApi,
  type ActionCatalogItem,
  type ModuleCatalogItem,
  type PermissionItem,
} from "@/features/admin-permissions/api/admin-permissions-api";
import { ApiError } from "@/services/http-client";

function grantKey(module: string, action: string): string {
  return `${module}:${action}`;
}

function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Error de red";
}

export function useUserPermissions(userId: string) {
  const [modules, setModules] = useState<ModuleCatalogItem[]>([]);
  const [actions, setActions] = useState<ActionCatalogItem[]>([]);
  const [granted, setGranted] = useState<Set<string>>(new Set());
  const [initialGranted, setInitialGranted] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [modulesResult, actionsResult, permissionsResult] = await Promise.all([
        adminPermissionsApi.modules(),
        adminPermissionsApi.actions(),
        adminPermissionsApi.getUserPermissions(userId),
      ]);
      setModules(modulesResult);
      setActions(actionsResult);
      const grantedSet = new Set(
        permissionsResult.grants.map((grant) => grantKey(grant.module, grant.action)),
      );
      setGranted(grantedSet);
      setInitialGranted(grantedSet);
    } catch (error) {
      toast.error(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    // fetch-on-mount/on-userId-change; `reload` flips `loading` synchronously
    // on purpose so the grid doesn't render stale data while refetching.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void reload();
  }, [reload]);

  function toggle(module: string, action: string): void {
    setGranted((current) => {
      const next = new Set(current);
      const k = grantKey(module, action);
      if (next.has(k)) {
        next.delete(k);
      } else {
        next.add(k);
      }
      return next;
    });
  }

  function isGranted(module: string, action: string): boolean {
    return granted.has(grantKey(module, action));
  }

  const dirty =
    granted.size !== initialGranted.size ||
    [...granted].some((k) => !initialGranted.has(k));

  async function save(): Promise<void> {
    setSaving(true);
    try {
      const grants: PermissionItem[] = [...granted].map((k) => {
        const [module, action] = k.split(":");
        return { module, action };
      });
      const response = await adminPermissionsApi.replaceUserPermissions(userId, grants);
      const grantedSet = new Set(
        response.grants.map((g) => grantKey(g.module, g.action)),
      );
      setGranted(grantedSet);
      setInitialGranted(grantedSet);
      toast.success("Permisos actualizados");
    } catch (error) {
      toast.error(errorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  return { modules, actions, isGranted, toggle, dirty, loading, saving, save };
}
