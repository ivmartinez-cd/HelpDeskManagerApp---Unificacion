"use client";

import { BrandModal } from "@/shared/components/ui/brand-modal";
import { ClientPickerProcessModal } from "./client-picker-process-modal";
import { ProyeccionTool } from "./proyeccion-tool";
import { CalculadoraTool } from "./calculadora-tool";
import { Db3Tool } from "./db3-tool";
import { En0Tool } from "./en0-tool";
import { SumaFijaTool } from "./suma-fija-tool";
import { TOOLS, type ToolKey } from "../tool-catalog";

function isToolKey(value: string | null): value is ToolKey {
  return TOOLS.some((tool) => tool.key === value);
}

const SIMPLE_WIDTH: Partial<Record<ToolKey, number>> = {
  proyeccion: 720,
  calc: 760,
  db3: 640,
  en0: 640,
  "suma-fija": 640,
};

interface Props {
  tool: string | null;
  onClose: () => void;
}

/** Decide, a partir de `?tool=`, qué modal mostrar sobre el hub "Centro de
 * Contadores" — las 5 herramientas de formulario simple entran directo acá;
 * SDS/ERS/FTP (que necesitan elegir un cliente primero) delegan en
 * client-picker-process-modal.tsx. */
export function ToolLauncherModal({ tool, onClose }: Props) {
  if (!isToolKey(tool)) return null;

  if (tool === "sds" || tool === "ers" || tool === "ftp") {
    return <ClientPickerProcessModal isOpen type={tool} onClose={onClose} />;
  }

  const def = TOOLS.find((t) => t.key === tool) ?? TOOLS[0];

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={def.navLabel ?? def.label}
      widthPx={SIMPLE_WIDTH[tool] ?? 640}
    >
      {tool === "proyeccion" && <ProyeccionTool />}
      {tool === "calc" && <CalculadoraTool />}
      {tool === "db3" && <Db3Tool />}
      {tool === "en0" && <En0Tool />}
      {tool === "suma-fija" && <SumaFijaTool />}
    </BrandModal>
  );
}
