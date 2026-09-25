"use client";

import { useState } from "react";
import { Settings } from "lucide-react";
import type { EstadoDashboard } from "../../hooks/use-reporte";
import { Button } from "@/shared/components/ui/button";
import { CLASE_BOTON } from "../tabla/estilos";
import { ModalCategorias } from "./modal-categorias";

/** Botón "Categorías" del encabezado (port de `ConfigButton`): abre la
 * configuración de la taxonomía. Solo para quien puede editar el módulo. */
export function BotonCategorias({ estado }: { estado: EstadoDashboard }) {
  const [abierto, setAbierto] = useState(false);
  if (!estado.canUpdate) return null;
  return (
    <>
      <Button
        variant="outline"
        className={CLASE_BOTON}
        onClick={() => setAbierto(true)}
        title="Configurar las categorías de incidentes"
      >
        <Settings className="h-4 w-4" aria-hidden="true" />
        Categorías
      </Button>
      <ModalCategorias isOpen={abierto} onClose={() => setAbierto(false)} onCambio={estado.recargar} />
    </>
  );
}
