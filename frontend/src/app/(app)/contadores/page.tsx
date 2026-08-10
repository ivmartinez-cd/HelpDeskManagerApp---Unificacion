"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ContadoresHub } from "@/features/contadores/components/contadores-hub";
import { ToolLauncherModal } from "@/features/contadores/components/tool-launcher-modal";
import { Spinner } from "@/shared/components/ui/spinner";

function ContadoresContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tool = searchParams.get("tool");

  return (
    <>
      <ContadoresHub />
      <ToolLauncherModal tool={tool} onClose={() => router.replace("/contadores")} />
    </>
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
