import { TurnosAdminTabs } from "@/features/turnos/components/admin/turnos-admin-tabs";

export const metadata = {
  title: "Turnos de Operadores",
};

export default function AdminTurnosPage() {
  return (
    <div className="p-6 lg:p-10">
      <div className="mb-8">
        <h1 className="font-heading text-2xl font-extrabold text-foreground">
          Turnos de Operadores
        </h1>
        <p className="mt-1 font-body text-sm text-muted-foreground">
          Gestión de casillas, franjas horarias y enroque de asignaciones de operadores. Modo
          vacaciones: grilla alternativa con vigencia, sin tocar la titular.
        </p>
      </div>

      <TurnosAdminTabs />
    </div>
  );
}
