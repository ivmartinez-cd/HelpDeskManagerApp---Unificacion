"use client";

import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import { Database, Download, FileCode } from "lucide-react";
import { contadoresApi, type Db3ExportResponse } from "../api/contadores-api";
import { Card, CardHeader, CardBody } from "@/shared/components/ui/card";
import { FileInput } from "@/shared/components/ui/file-input";
import { Input } from "@/shared/components/ui/input";
import { Button, buttonClasses } from "@/shared/components/ui/button";
import { StatCard } from "@/shared/components/ui/stat-card";

export function Db3Tool() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [fechaMaxima, setFechaMaxima] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Db3ExportResponse | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!files || files.length === 0) {
      toast.error("Por favor seleccioná al menos un archivo SQLite (.db3)");
      return;
    }

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }
    if (fechaMaxima) {
      formData.append("fecha_maxima", fechaMaxima);
    }

    setLoading(true);
    setResult(null);

    try {
      const res = await contadoresApi.runDb3Export(formData);
      setResult(res);
      toast.success("Bases de datos DB3 procesadas con éxito");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error al procesar archivos DB3";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader title="Consolidación de Archivos DB3 a CSV" icon={Database} />
        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid gap-5 md:grid-cols-2">
              <FileInput
                id="db3-files"
                label="Archivos SQLite (.db3)"
                accept=".db3,.sqlite"
                multiple
                onChange={(e) => setFiles(e.target.files)}
                hint="Podés seleccionar múltiples archivos .db3 simultáneamente."
                required
              />
              <Input
                id="db3-fecha-maxima"
                label="Fecha Máxima de Lectura (Opcional)"
                type="date"
                value={fechaMaxima}
                onChange={(e) => setFechaMaxima(e.target.value)}
              />
            </div>

            <Button type="submit" loading={loading}>
              <FileCode className="h-4 w-4" />
              Procesar DB3 a CSV
            </Button>
          </form>
        </CardBody>
      </Card>

      {result && (
        <Card>
          <CardHeader title="Resultado de Consolidación" />
          <CardBody className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label="Total Filas Generadas" value={result.total_rows} />
              <StatCard label="Clase 10 (Mono)" value={result.counterclass_10_count} tone="info" />
              <StatCard
                label="Clase 20 (Color)"
                value={result.counterclass_20_count}
                tone="accent"
              />
              <StatCard
                label="Clase 40 (Duplicados)"
                value={result.counterclass_40_count}
                tone="warning"
              />
            </div>

            <a
              href={contadoresApi.getOutputUrl(result.csv_filename)}
              download={result.csv_filename}
              className={buttonClasses({ variant: "success" })}
            >
              <Download className="h-4 w-4" />
              Descargar Archivo CSV Consolidado (.csv)
            </a>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
