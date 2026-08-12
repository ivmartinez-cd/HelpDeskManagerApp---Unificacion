interface ContactSummaryProps {
  label: string;
  apellido: string;
  nombre: string;
  email: string;
  telefono: string;
}

/** Resumen de un contacto (Solicitante o Destinatario) dentro de la card de
 * zona del modal de Contactos. */
export function ContactSummary({ label, apellido, nombre, email, telefono }: ContactSummaryProps) {
  const name = [apellido, nombre].filter(Boolean).join(", ");
  return (
    <div>
      <p className="font-body text-[10px] font-bold uppercase tracking-wide text-muted-foreground">{label}</p>
      {name ? <p className="font-body text-xs text-foreground">{name}</p> : null}
      {email ? <p className="font-body text-xs text-muted-foreground">{email}</p> : null}
      {telefono ? <p className="font-body text-xs text-muted-foreground">{telefono}</p> : null}
    </div>
  );
}
