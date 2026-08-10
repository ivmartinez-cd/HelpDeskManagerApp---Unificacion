"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  ContadoresHeader,
  TOOLS,
  type ToolKey,
} from "@/features/contadores/components/contadores-header";
import { ProyeccionTool } from "@/features/contadores/components/proyeccion-tool";
import { CalculadoraTool } from "@/features/contadores/components/calculadora-tool";
import { Db3Tool } from "@/features/contadores/components/db3-tool";
import { En0Tool } from "@/features/contadores/components/en0-tool";
import { SumaFijaTool } from "@/features/contadores/components/suma-fija-tool";
import { FtpClientsTool } from "@/features/contadores/components/ftp-clients-tool";
import { SdsTool } from "@/features/contadores/components/sds-tool";
import { ErsTool } from "@/features/contadores/components/ers-tool";
import { Spinner } from "@/shared/components/ui/spinner";

const DEFAULT_TOOL: ToolKey = "proyeccion";

function isToolKey(value: string | null): value is ToolKey {
  return TOOLS.some((tool) => tool.key === value);
}

function ContadoresContent() {
  const searchParams = useSearchParams();
  const requestedTool = searchParams.get("tool");
  const activeTool = isToolKey(requestedTool) ? requestedTool : DEFAULT_TOOL;

  return (
    <div className="min-h-full bg-background pb-12">
      <ContadoresHeader activeTool={activeTool} />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {activeTool === "proyeccion" && <ProyeccionTool />}
        {activeTool === "calc" && <CalculadoraTool />}
        {activeTool === "db3" && <Db3Tool />}
        {activeTool === "en0" && <En0Tool />}
        {activeTool === "suma-fija" && <SumaFijaTool />}
        {activeTool === "ftp" && <FtpClientsTool />}
        {activeTool === "sds" && <SdsTool />}
        {activeTool === "ers" && <ErsTool />}
      </main>
    </div>
  );
}

export default function ContadoresPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-64 items-center justify-center">
          <Spinner />
        </div>
      }
    >
      <ContadoresContent />
    </Suspense>
  );
}
