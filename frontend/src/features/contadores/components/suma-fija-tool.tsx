"use client";

import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import { Download, Sigma } from "lucide-react";
import { contadoresApi, type FixedSumResponse } from "../api/contadores-api";
import { Card, CardHeader, CardBody } from "@/shared/components/ui/card";
import { FileInput } from "@/shared/components/ui/file-input";
import { Input } from "@/shared/components/ui/input";
import { Button, buttonClasses } from "@/shared/components/ui/button";
import { StatCard } from "@/shared/components/ui/stat-card";

export function SumaFijaTool() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [fecha, setFecha] = useState(new Date().toISOString().split("T")[0]);
  const [hojas, setHojas] = useState<number | "">(500);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FixedSumResponse | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!files || files.length === 0 || !fecha || hojas === "") {
      toast.error("Por favor completá todos los campos requeridos");
      return;
    }

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }
    formData.append("fecha", fecha);
    formData.append("hojas", String(hojas));

    setLoading(true);
    setResult(null);

    try {
      const res = await contadoresApi.runFixedSum(formData);
      setResult(res);
      toast.success("Archivos de Suma Fija procesados con éxito");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error al procesar la Suma Fija";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader title="Procesamiento de Suma Fija en Excel" icon={Sigma} />
        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid gap-5 md:grid-cols-3">
              <FileInput
                id="suma-fija-files"
                label="Archivos Excel (.xlsx)"
                accept=".xlsx"
                multiple
                onChange={(e) => setFiles(e.target.files)}
                required
              />
              <Input
                id="suma-fija-fecha"
                label="Fecha de Lectura"
                type="date"
                value={fecha}
                onChange={(e) => setFecha(e.target.value)}
                required
              />
              <Input
                id="suma-fija-hojas"
                label="Hojas a Sumar"
                type="number"
                min="1"
                value={hojas}
                onChange={(e) => setHojas(e.target.value === "" ? "" : Number(e.target.value))}
                placeholder="Ej: 500"
                required
              />
            </div>

            <Button type="submit" loading={loading}>
              <Sigma className="h-4 w-4" />
              Procesar Suma Fija
            </Button>
          </form>
        </CardBody>
      </Card>

      {result && (
        <Card>
          <CardHeader title="Resultado del Procesamiento" />
          <CardBody className="space-y-6">
            <div className="max-w-xs">
              <StatCard label="Total Filas Generadas" value={result.total_rows} />
            </div>

            <div className="space-y-3">
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Archivos CSV Generados ({result.csv_filenames.length}):
              </p>
              <div className="flex flex-wrap gap-3">
                {result.csv_filenames.map((fname) => (
                  <a
                    key={fname}
                    href={contadoresApi.getOutputUrl(fname)}
                    download={fname}
                    className={buttonClasses({ variant: "success", size: "sm" })}
                  >
                    <Download className="h-4 w-4" />
                    Descargar {fname}
                  </a>
                ))}
              </div>
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
