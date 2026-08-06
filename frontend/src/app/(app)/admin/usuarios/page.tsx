"use client";

import { useState } from "react";
import Link from "next/link";
import { KeyRound, Plus, Shield, ShieldOff, Sliders } from "lucide-react";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
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
          <h1 className="text-2xl font-black uppercase tracking-tight">Usuarios</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {total} usuario{total === 1 ? "" : "s"} registrado{total === 1 ? "" : "s"}.
          </p>
        </div>
        <Button onClick={() => setModalOpen(true)}>
          <Plus className="h-4 w-4" />
          Nuevo usuario
        </Button>
      </div>

      <div className="mb-4 max-w-sm">
        <Input
          placeholder="Buscar por nombre o email…"
          value={query}
          onChange={(event) => search(event.target.value)}
        />
      </div>

      <div className="overflow-x-auto rounded-2xl border border-black/10 dark:border-white/10 bg-card">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-black/10 dark:border-white/10 text-xs font-black uppercase tracking-wide text-muted-foreground">
              <th className="px-4 py-3">Usuario</th>
              <th className="px-4 py-3">Rol</th>
              <th className="px-4 py-3">Estado</th>
              <th className="px-4 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {!loading && items.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-10 text-center text-muted-foreground">
                  No se encontraron usuarios.
                </td>
              </tr>
            )}
            {items.map((item) => (
              <tr
                key={item.id}
                className="border-b border-black/5 dark:border-white/5 last:border-0"
              >
                <td className="px-4 py-3">
                  <p className="font-bold">{item.fullName}</p>
                  <p className="text-xs text-muted-foreground">{item.email}</p>
                </td>
                <td className="px-4 py-3">
                  <Badge variant={item.isSuperadmin ? "accent" : "neutral"}>
                    {item.isSuperadmin ? "Superadmin" : "Usuario"}
                  </Badge>
                </td>
                <td className="px-4 py-3">
                  <Badge variant={item.isActive ? "success" : "danger"}>
                    {item.isActive ? "Activo" : "Inactivo"}
                  </Badge>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-1.5">
                    <Link href={`/admin/usuarios/${item.id}/permisos`}>
                      <Button variant="outline" size="icon" title="Permisos">
                        <Sliders className="h-4 w-4" />
                      </Button>
                    </Link>
                    <Button
                      variant="outline"
                      size="icon"
                      title="Enviar link de restablecimiento"
                      onClick={() => void triggerPasswordReset(item)}
                    >
                      <KeyRound className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      title={item.isActive ? "Desactivar" : "Activar"}
                      disabled={item.id === currentUser.id}
                      onClick={() => void toggleActive(item)}
                    >
                      {item.isActive ? (
                        <ShieldOff className="h-4 w-4" />
                      ) : (
                        <Shield className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-center gap-3 text-sm">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
          >
            Anterior
          </Button>
          <span className="text-muted-foreground">
            Página {page} de {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
          >
            Siguiente
          </Button>
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
