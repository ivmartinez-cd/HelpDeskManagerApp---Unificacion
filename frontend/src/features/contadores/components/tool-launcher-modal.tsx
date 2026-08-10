"use client";

import { BrandModal } from "@/shared/components/ui/brand-modal";
import { CalendarioTool } from "./calendario-tool";
import { ClientPickerProcessModal } from "./client-picker-process-modal";
import { Db3Tool } from "./db3-tool";
import { En0Tool } from "./en0-tool";
import { SumaFijaTool } from "./suma-fija-tool";
import { TOOLS, type ToolKey } from "../tool-catalog";

function isToolKey(value: string | null): value is ToolKey {
  return TOOLS.some((tool) => tool.key === value);
}

const SIMPLE_WIDTH: Partial<Record<ToolKey, number>> = {
  db3: 640,
  en0: 640,
  "suma-fija": 640,
  calendario: 1000,
};

interface Props {
  tool: string | null;
  onClose: () => void;
}

export function ToolLauncherModal({ tool, onClose }: Props) {
  if (!isToolKey(tool)) return null;

  const def = TOOLS.find((t) => t.key === tool) ?? TOOLS[0];
  if (def.disabled) return null;

  if (tool === "sds" || tool === "ers" || tool === "ftp") {
    return <ClientPickerProcessModal isOpen type={tool} onClose={onClose} />;
  }

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={def.navLabel ?? def.label}
      widthPx={SIMPLE_WIDTH[tool] ?? 640}
    >
      {tool === "calendario" && <CalendarioTool />}
      {tool === "db3" && <Db3Tool />}
      {tool === "en0" && <En0Tool />}
      {tool === "suma-fija" && <SumaFijaTool />}
    </BrandModal>
  );
}

