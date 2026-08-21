"use client";

import { Fragment, use, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { adminUsersApi, type AdminUser } from "@/features/admin-users/api/admin-users-api";
import { PERMISSION_TEMPLATES } from "@/features/admin-permissions/config/permission-templates";
import { useUserPermissions } from "@/features/admin-permissions/hooks/use-user-permissions";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { ApiError } from "@/services/http-client";
import { toast } from "sonner";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function UserPermissionsPage({ params }: PageProps) {
  const { id } = use(params);
  const [targetUser, setTargetUser] = useState<AdminUser | null>(null);
  const {
    modules,
    actions,
    features,
    isGranted,
    hasFeature,
    toggle,
    toggleFeature,
    applyTemplate,
    clearAll,
    dirty,
    loading,
    saving,
    save,
  } = useUserPermissions(id);

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
        className="mb-4 inline-flex items-center gap-1.5 font-body text-xs font-bold uppercase tracking-wide text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Usuarios
      </Link>

      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-heading text-2xl font-extrabold text-foreground">Permisos</h1>
          <p className="mt-1 font-body text-sm text-muted-foreground">
            {targetUser ? `${targetUser.fullName} · ${targetUser.email}` : "Cargando usuario…"}
          </p>
        </div>
        <BrandButton onClick={() => void save()} loading={saving} disabled={!dirty}>
          Guardar cambios
        </BrandButton>
      </div>

      {targetUser?.isSuperadmin && (
        <p className="mb-4 rounded-[10px] bg-brand-orange/10 px-4 py-3 font-body text-xs font-bold uppercase tracking-wide text-brand-orange">
          Este usuario es Administrador (superadmin): ya tiene acceso a todo, sin importar esta grilla.
        </p>
      )}

      {!loading && (
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <span className="font-body text-xs font-bold uppercase tracking-wide text-muted-foreground">
            Aplicar perfil
          </span>
          {PERMISSION_TEMPLATES.map((template) => (
            <BrandButton
              key={template.key}
              size="sm"
              variant="outline"
              title={template.description}
              onClick={() => applyTemplate(template.grants, template.features)}
            >
              {template.label}
            </BrandButton>
          ))}
          <BrandButton size="sm" variant="outline" onClick={clearAll} title="Destildar todo">
            Quitar todo
          </BrandButton>
          <span className="font-body text-xs text-muted-foreground">
            Las plantillas reemplazan la selección; revisá la grilla y guardá.
          </span>
        </div>
      )}

      {!loading && (
        <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
          <table className="w-full text-left font-body text-sm">
            <thead>
              <tr className="border-b border-border text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
                <th className="px-4 py-3">Módulo</th>
                {/* Sin columna "Alcance": `user_module_scope` (alcance por sector)
                    existe en la DB pero no tiene lógica (ADR-029, deuda conocida);
                    mostrar un select deshabilitado solo confundía al admin. */}
                {actions.map((action) => (
                  <th key={action.key} className="px-4 py-3 text-center">
                    {action.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {modules.map((module) => {
                const funciones = features.filter((f) => f.module === module.key);
                return (
                <Fragment key={module.key}>
                <tr className={funciones.length === 0 ? "border-b border-border last:border-0" : ""}>
                  <td className="px-4 py-3">
                    <p className="font-semibold text-foreground">{module.label}</p>
                    {!module.isEnabled && (
                      <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
                        Módulo aún no habilitado
                      </p>
                    )}
                  </td>
                  {actions.map((action) => {
                    const applicable = module.actions.includes(action.key);
                    return (
                      <td key={action.key} className="px-4 py-3 text-center">
                        {applicable ? (
                          <input
                            type="checkbox"
                            className="h-4 w-4 accent-brand-orange"
                            checked={isGranted(module.key, action.key)}
                            disabled={targetUser?.isSuperadmin}
                            onChange={() => toggle(module.key, action.key)}
                            aria-label={`${module.label} · ${action.label}`}
                          />
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
                {funciones.length > 0 && (
                  <tr className="border-b border-border last:border-0 bg-muted/20">
                    <td className="px-4 pb-3 pt-1 align-top">
                      <p className="text-[10px] font-bold uppercase tracking-wide text-muted-foreground">
                        Pantallas y funciones
                      </p>
                    </td>
                    <td className="px-4 pb-3 pt-1" colSpan={actions.length}>
                      <div className="flex flex-wrap gap-x-5 gap-y-1.5">
                        {funciones.map((f) => (
                          <label
                            key={f.key}
                            title={f.description}
                            className="inline-flex cursor-pointer items-center gap-2 font-body text-xs text-foreground"
                          >
                            <input
                              type="checkbox"
                              className="h-3.5 w-3.5 accent-brand-orange"
                              checked={hasFeature(f.key)}
                              disabled={targetUser?.isSuperadmin}
                              onChange={() => toggleFeature(f.key)}
                              aria-label={`${module.label} · ${f.label}`}
                            />
                            {f.label}
                          </label>
                        ))}
                      </div>
                    </td>
                  </tr>
                )}
                </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
