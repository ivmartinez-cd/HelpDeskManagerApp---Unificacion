"use client";

import { useState } from "react";
import Link from "next/link";
import { KeyRound, Plus, Shield, ShieldOff, Sliders } from "lucide-react";
import { BrandBadge, BrandButton, BrandEmptyState, BrandInput } from "@/shared/components/ui/brand-form";
import { CreateUserModal } from "@/features/admin-users/components/create-user-modal";
import { useAdminUsers } from "@/features/admin-users/hooks/use-admin-users";
import { useSession } from "@/services/session-provider";

export default function AdminUsersPage() {
  const {
    items,
    total,
    page,
    setPage,
    query,
    search,
    loading,
    pageSize,
    createUser,
    toggleActive,
    triggerPasswordReset,
  } = useAdminUsers();
  const { user: currentUser } = useSession();
  const [modalOpen, setModalOpen] = useState(false);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="p-6 lg:p-10">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-heading text-2xl font-extrabold text-brand-charcoal">Usuarios</h1>
          <p className="mt-1 font-body text-sm text-[#8a8a8a]">
            {total} usuario{total === 1 ? "" : "s"} registrado{total === 1 ? "" : "s"}.
          </p>
        </div>
        <BrandButton onClick={() => setModalOpen(true)}>
          <Plus className="h-4 w-4" />
          Nuevo usuario
        </BrandButton>
      </div>

      <div className="mb-4 max-w-sm">
        <BrandInput
          label="Buscar"
          placeholder="Buscar por nombre o email…"
          value={query}
          onChange={(event) => search(event.target.value)}
        />
      </div>

      {!loading && items.length === 0 ? (
        <BrandEmptyState icon={Shield} title="No se encontraron usuarios." />
      ) : (
        <div className="overflow-x-auto rounded-[12px] border border-black/[0.08] bg-white">
          <table className="w-full text-left font-body text-sm">
            <thead>
              <tr className="border-b border-black/[0.08] text-[11px] font-bold uppercase tracking-wide text-[#7a7a7a]">
                <th className="px-4 py-3">Usuario</th>
                <th className="px-4 py-3">Rol</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-b border-black/[0.05] last:border-0">
                  <td className="px-4 py-3">
                    <p className="font-semibold text-brand-charcoal">{item.fullName}</p>
                    <p className="text-xs text-[#9a9a9a]">{item.email}</p>
                  </td>
                  <td className="px-4 py-3">
                    <BrandBadge variant={item.isSuperadmin ? "accent" : "neutral"}>
                      {item.isSuperadmin ? "Superadmin" : "Usuario"}
                    </BrandBadge>
                  </td>
                  <td className="px-4 py-3">
                    <BrandBadge variant={item.isActive ? "success" : "danger"}>
                      {item.isActive ? "Activo" : "Inactivo"}
                    </BrandBadge>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1.5">
                      <Link
                        href={`/admin/usuarios/${item.id}/permisos`}
                        title="Permisos"
                        className="rounded-[8px] border border-black/[0.14] p-2 text-brand-charcoal transition-colors hover:bg-black/5"
                      >
                        <Sliders className="h-4 w-4" />
                      </Link>
                      <button
                        type="button"
                        title="Enviar link de restablecimiento"
                        className="rounded-[8px] border border-black/[0.14] p-2 text-brand-charcoal transition-colors hover:bg-black/5"
                        onClick={() => void triggerPasswordReset(item)}
                      >
                        <KeyRound className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        title={item.isActive ? "Desactivar" : "Activar"}
                        disabled={item.id === currentUser.id}
                        className="rounded-[8px] border border-black/[0.14] p-2 text-brand-charcoal transition-colors hover:bg-black/5 disabled:opacity-40"
                        onClick={() => void toggleActive(item)}
                      >
                        {item.isActive ? (
                          <ShieldOff className="h-4 w-4" />
                        ) : (
                          <Shield className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-center gap-3 font-body text-sm">
          <BrandButton
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
          >
            Anterior
          </BrandButton>
          <span className="text-[#8a8a8a]">
            Página {page} de {totalPages}
          </span>
          <BrandButton
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
          >
            Siguiente
          </BrandButton>
        </div>
      )}

      <CreateUserModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreate={createUser}
      />
    </div>
  );
}
