"use client";

import { useState } from "react";
import { Inbox } from "lucide-react";
import { BrandEmptyState } from "@/shared/components/ui/brand-form";
import { PaginationBar } from "@/shared/components/ui/pagination-bar";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import type { EstadoReporte } from "../api/reportes-app-api";
import { useReportes } from "../hooks/use-reportes";
import { ETIQUETA_ESTADO, ReporteCard } from "./reporte-card";

const FILTROS = [
  { value: "propuesto", label: ETIQUETA_ESTADO.propuesto },
  { value: "nuevo", label: "Nuevos" },
  { value: "aprobado", label: "Aprobados" },
  { value: "en_curso", label: ETIQUETA_ESTADO.en_curso },
  { value: "resuelto", label: "Resueltos" },
  { value: "integrar", label: ETIQUETA_ESTADO.integrar },
  { value: "integrado", label: "Integrados" },
  { value: "descartado", label: "Descartados" },
  { value: "todos", label: "Todos" },
];
const SIZE = 20;

/** Panel del superadmin: cada reporte tal como llegó, con la propuesta que
 * dejó Claude por el servidor MCP, y la decisión (aprobar / pedir cambios /
 * descartar) para los que esperan su OK. */
export function ReportesPanel() {
  const [filtro, setFiltro] = useState("propuesto");
  const [page, setPage] = useState(1);
  const estado = filtro === "todos" ? null : (filtro as EstadoReporte);
  const { datos, loading, error, refetch } = useReportes(estado, page, SIZE);

  return (
    <div className="p-6 lg:p-10">
      <h1 className="font-heading text-2xl font-extrabold text-foreground">
        Reportes de la app
      </h1>
      <p className="mt-1 mb-6 font-body text-sm text-muted-foreground">
        Errores y mejoras que cargan los usuarios con el botón de reportar, y lo
        que propone Claude para cada uno.
      </p>
      <div className="mb-4 overflow-x-auto">
        <SegmentedControl
          label="Filtrar por estado"
          options={FILTROS}
          value={filtro}
          onChange={(v) => {
            setFiltro(v);
            setPage(1);
          }}
        />
      </div>
      {error && (
        <p className="mb-4 font-body text-sm font-semibold text-destructive">
          {error}
        </p>
      )}
      {!loading && datos.items.length === 0 ? (
        <BrandEmptyState icon={Inbox} title="No hay reportes en este estado" />
      ) : (
        <div className="flex flex-col gap-4">
          {datos.items.map((r) => (
            <ReporteCard
              key={r.id}
              reporte={r}
              onDecidido={() => void refetch()}
            />
          ))}
        </div>
      )}
      <PaginationBar
        className="mt-4"
        page={page}
        total={datos.total}
        size={SIZE}
        onPageChange={setPage}
        noun="reportes"
      />
    </div>
  );
}
