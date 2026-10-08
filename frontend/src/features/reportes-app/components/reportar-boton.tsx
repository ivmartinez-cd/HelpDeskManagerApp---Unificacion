"use client";

import { useState } from "react";
import { MessageSquareWarning } from "lucide-react";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { ReportarForm } from "./reportar-form";

/** Botón del header para cargar un error o una mejora desde cualquier pantalla. */
export function ReportarBoton() {
  const [abierto, setAbierto] = useState(false);
  return (
    <>
      <button
        onClick={() => setAbierto(true)}
        className="rounded-[8px] p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
        title="Reportar un error o una mejora"
        aria-label="Reportar un error o una mejora"
      >
        <MessageSquareWarning className="h-5 w-5" />
      </button>
      <BrandModal
        isOpen={abierto}
        onClose={() => setAbierto(false)}
        title="Reportar error o mejora"
      >
        <ReportarForm onEnviado={() => setAbierto(false)} />
      </BrandModal>
    </>
  );
}
