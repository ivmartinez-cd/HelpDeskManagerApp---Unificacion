import Link from "next/link";
import { Users } from "lucide-react";

export default function AdminHomePage() {
  return (
    <div className="p-6 lg:p-10">
      <div className="mb-8">
        <h1 className="text-2xl font-black uppercase tracking-tight">Configuración</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Administración de usuarios y permisos de la plataforma.
        </p>
      </div>
      <Link
        href="/admin/usuarios"
        className="flex max-w-sm items-center gap-4 rounded-2xl border border-black/10 dark:border-white/10 bg-card p-6 transition-colors hover:bg-black/5 dark:hover:bg-white/5"
      >
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-accent/10 text-accent">
          <Users className="h-6 w-6" />
        </div>
        <div>
          <p className="font-black uppercase tracking-wide">Usuarios</p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Crear cuentas, activar/desactivar y asignar permisos.
          </p>
        </div>
      </Link>
    </div>
  );
}
