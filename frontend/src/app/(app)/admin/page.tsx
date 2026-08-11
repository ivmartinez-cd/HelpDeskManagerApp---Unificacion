import Link from "next/link";
import { Clock, Users } from "lucide-react";

export const metadata = {
  title: "Configuración",
};

export default function AdminHomePage() {
  return (
    <div className="p-6 lg:p-10">
      <div className="mb-8">
        <h1 className="font-heading text-2xl font-extrabold text-foreground">
          Configuración
        </h1>
        <p className="mt-1 font-body text-sm text-muted-foreground">
          Administración de usuarios, permisos y turnos de operadores.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-4xl">
        <Link
          href="/admin/usuarios"
          className="flex items-center gap-4 rounded-[12px] border border-border bg-card p-6 transition-colors hover:bg-muted"
        >
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-[9px] bg-brand-orange/[0.12] text-brand-orange">
            <Users className="h-6 w-6" />
          </div>
          <div>
            <p className="font-heading text-sm font-bold text-foreground">Usuarios</p>
            <p className="mt-0.5 font-body text-xs text-muted-foreground">
              Crear cuentas, activar/desactivar y asignar permisos.
            </p>
          </div>
        </Link>

        <Link
          href="/admin/turnos"
          className="flex items-center gap-4 rounded-[12px] border border-border bg-card p-6 transition-colors hover:bg-muted"
        >
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-[9px] bg-brand-orange/[0.12] text-brand-orange">
            <Clock className="h-6 w-6" />
          </div>
          <div>
            <p className="font-heading text-sm font-bold text-foreground">Turnos de Operadores</p>
            <p className="mt-0.5 font-body text-xs text-muted-foreground">
              Casillas, franjas horarias y enroque de operadores.
            </p>
          </div>
        </Link>
      </div>
    </div>
  );
}
