"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { adminUsersApi, type AdminUser } from "@/features/admin-users/api/admin-users-api";
import { useUserPermissions } from "@/features/admin-permissions/hooks/use-user-permissions";
import { Button } from "@/shared/components/ui/button";
import { ApiError } from "@/services/http-client";
import { toast } from "sonner";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function UserPermissionsPage({ params }: PageProps) {
  const { id } = use(params);
  const [targetUser, setTargetUser] = useState<AdminUser | null>(null);
  const { modules, actions, isGranted, toggle, dirty, loading, saving, save } =
    useUserPermissions(id);

  useEffect(() => {
    adminUsersApi
      .get(id)
      .then(setTargetUser)
      .catch((error: unknown) => {
        toast.error(error instanceof ApiError ? error.message : "Error de red");
      });
  }, [id]);

  return (
    <div className="p-6 lg:p-10">
      <Link
        href="/admin/usuarios"
        className="mb-4 inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Usuarios
      </Link>

      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black uppercase tracking-tight">Permisos</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {targetUser ? `${targetUser.fullName} · ${targetUser.email}` : "Cargando usuario…"}
          </p>
        </div>
        <Button onClick={() => void save()} loading={saving} disabled={!dirty}>
          Guardar cambios
        </Button>
      </div>

      {targetUser?.isSuperadmin && (
        <p className="mb-4 rounded-xl bg-accent/10 px-4 py-3 text-xs font-bold uppercase tracking-wide text-accent">
          Este usuario es superadmin: ya tiene acceso a todo, sin importar esta grilla.
        </p>
      )}

      {!loading && (
        <div className="overflow-x-auto rounded-2xl border border-black/10 dark:border-white/10 bg-card">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-black/10 dark:border-white/10 text-xs font-black uppercase tracking-wide text-muted-foreground">
                <th className="px-4 py-3">Módulo</th>
                <th className="px-4 py-3">Alcance</th>
                {actions.map((action) => (
                  <th key={action.key} className="px-4 py-3 text-center">
                    {action.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {modules.map((module) => (
                <tr
                  key={module.key}
                  className="border-b border-black/5 dark:border-white/5 last:border-0"
                >
                  <td className="px-4 py-3">
                    <p className="font-bold">{module.label}</p>
                    {!module.isEnabled && (
                      <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
                        Módulo aún no habilitado
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <select
                      disabled
                      title="El alcance por sector se activa cuando se migre el módulo de vacaciones"
                      className="rounded-lg border border-black/10 dark:border-white/10 bg-background px-2 py-1 text-xs text-muted-foreground disabled:opacity-50"
                    >
                      <option>Global</option>
                    </select>
                  </td>
                  {actions.map((action) => {
                    const applicable = module.actions.includes(action.key);
                    return (
                      <td key={action.key} className="px-4 py-3 text-center">
                        {applicable ? (
                          <input
                            type="checkbox"
                            className="h-4 w-4 accent-[var(--accent)]"
                            checked={isGranted(module.key, action.key)}
                            disabled={targetUser?.isSuperadmin}
                            onChange={() => toggle(module.key, action.key)}
                            aria-label={`${module.label} · ${action.label}`}
                          />
                        ) : (
                          <span className="text-muted-foreground/30">—</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
