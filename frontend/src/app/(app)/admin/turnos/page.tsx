import { CasillasManager } from "@/features/turnos/components/admin/casillas-manager";

export const metadata = {
  title: "Turnos de Operadores",
};

export default function AdminTurnosPage() {
  return (
    <div className="p-6 lg:p-10">
      <div className="mb-8">
        <h1 className="font-heading text-2xl font-extrabold text-foreground">
          Configuración de Turnos de Operadores
        </h1>
        <p className="mt-1 font-body text-sm text-muted-foreground">
          Gestión de casillas, franjas horarias y enroque de asignaciones de operadores.
        </p>
      </div>

      <CasillasManager />
    </div>
  );
}
