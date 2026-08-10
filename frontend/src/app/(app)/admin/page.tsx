import Link from "next/link";
import { Users } from "lucide-react";

export const metadata = {
  title: "Configuración",
};

export default function AdminHomePage() {
  return (
    <div className="p-6 lg:p-10">
      <div className="mb-8">
        <h1 className="font-heading text-2xl font-extrabold text-brand-charcoal">
          Configuración
        </h1>
        <p className="mt-1 font-body text-sm text-[#8a8a8a]">
          Administración de usuarios y permisos de la plataforma.
        </p>
      </div>
      <Link
        href="/admin/usuarios"
        className="flex max-w-sm items-center gap-4 rounded-[12px] border border-black/[0.08] bg-white p-6 transition-colors hover:bg-black/[0.02]"
      >
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-[9px] bg-brand-orange/[0.12] text-brand-orange">
          <Users className="h-6 w-6" />
        </div>
        <div>
          <p className="font-heading text-sm font-bold text-brand-charcoal">Usuarios</p>
          <p className="mt-0.5 font-body text-xs text-[#8a8a8a]">
            Crear cuentas, activar/desactivar y asignar permisos.
          </p>
        </div>
      </Link>
    </div>
  );
}
