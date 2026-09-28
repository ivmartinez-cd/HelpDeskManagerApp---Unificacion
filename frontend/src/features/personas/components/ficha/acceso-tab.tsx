"use client";

import { useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { KeyRound, Sliders } from "lucide-react";
import { adminUsersApi } from "@/features/admin-users/api/admin-users-api";
import { ApiError } from "@/services/http-client";
import { useSession } from "@/services/session-provider";
import { BrandBadge, BrandButton, brandButtonClasses } from "@/shared/components/ui/brand-form";
import { personasApi, type Persona } from "../../api/personas-api";

interface Props {
  persona: Persona;
  onCambio: (persona: Persona) => void;
}

function mensaje(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback;
}

function formatIngreso(iso: string | null): string {
  if (!iso) return "Nunca entró";
  return new Date(iso).toLocaleString("es-AR", { dateStyle: "short", timeStyle: "short" });
}

/** Acceso a la app (personas.manage). Permisos y "restablecer contraseña"
 * siguen siendo de Administración (admin.manage). */
export function AccesoTab({ persona, onCambio }: Props) {
  const { user, can } = useSession();
  const esAdmin = can("admin", "manage");
  const [busy, setBusy] = useState(false);
  const acceso = persona.acceso;
  const esUnoMismo = acceso?.userId === user.id;

  const ejecutar = (accion: () => Promise<Persona>, ok: string, fallback: string) => {
    setBusy(true);
    accion()
      .then((p) => {
        toast.success(ok);
        onCambio(p);
      })
      .catch((err: unknown) => toast.error(mensaje(err, fallback)))
      .finally(() => setBusy(false));
  };

  const darAcceso = () =>
    ejecutar(
      () => personasApi.darAcceso(persona.id),
      acceso ? "Acceso reactivado" : `Acceso creado. Se envió el link de activación a ${persona.email}.`,
      "No se pudo dar acceso.",
    );

  const quitarAcceso = () => {
    if (!window.confirm(`¿Quitarle el acceso a la app a ${persona.firstName}? No va a poder iniciar sesión.`)) return;
    ejecutar(() => personasApi.quitarAcceso(persona.id), "Acceso quitado", "No se pudo quitar el acceso.");
  };

  const enviarReset = () => {
    if (!acceso) return;
    adminUsersApi
      .triggerPasswordReset(acceso.userId)
      .then(() => toast.success(`Se envió un link de restablecimiento a ${persona.email}`))
      .catch((err: unknown) => toast.error(mensaje(err, "No se pudo enviar el link.")));
  };

  return (
    <div className="flex max-w-[560px] flex-col gap-5">
      <div className="flex flex-col gap-2 rounded-[12px] border border-border px-5 py-4 font-body text-sm">
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">Estado:</span>
          <BrandBadge variant={persona.entraALaApp ? "success" : "neutral"}>
            {persona.entraALaApp ? "Entra a la app" : acceso ? "Acceso quitado" : "Sin acceso"}
          </BrandBadge>
          {acceso?.superadmin && <BrandBadge variant="accent">Administrador</BrandBadge>}
        </div>
        {acceso && (
          <p className="text-muted-foreground">
            Último ingreso: <span className="text-foreground">{formatIngreso(acceso.ultimoIngreso)}</span>
          </p>
        )}
        <p className="text-muted-foreground">
          Inicia sesión con <span className="text-foreground">{persona.email}</span>
        </p>
      </div>

      {!persona.activa && !persona.entraALaApp && (
        <p className="font-body text-xs text-muted-foreground">
          La persona está inactiva: para darle acceso, primero pasala a activa en la pestaña Laboral.
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        {persona.entraALaApp ? (
          <BrandButton
            variant="outline"
            onClick={quitarAcceso}
            loading={busy}
            disabled={esUnoMismo}
            title={esUnoMismo ? "No podés quitarte el acceso a vos mismo" : undefined}
            className="border-destructive/40 text-destructive hover:bg-destructive/10"
          >
            Quitar acceso
          </BrandButton>
        ) : (
          <BrandButton onClick={darAcceso} loading={busy} disabled={!persona.activa}>
            {acceso ? "Reactivar acceso" : "Dar acceso a la app"}
          </BrandButton>
        )}
        {esAdmin && acceso && (
          <>
            <Link href={`/admin/usuarios/${acceso.userId}/permisos`} className={brandButtonClasses({ variant: "outline" })}>
              <Sliders className="h-4 w-4" />
              Permisos
            </Link>
            {persona.entraALaApp && (
              <BrandButton variant="outline" onClick={enviarReset}>
                <KeyRound className="h-4 w-4" />
                Enviar link de restablecimiento
              </BrandButton>
            )}
          </>
        )}
      </div>
    </div>
  );
}
