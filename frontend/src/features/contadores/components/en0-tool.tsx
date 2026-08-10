"use client";

import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import { Download, FileSpreadsheet } from "lucide-react";
import { contadoresApi, type EstimationZeroResponse } from "../api/contadores-api";
import { Card, CardHeader, CardBody } from "@/shared/components/ui/card";
import { FileInput } from "@/shared/components/ui/file-input";
import { Input } from "@/shared/components/ui/input";
import { Button, buttonClasses } from "@/shared/components/ui/button";
import { StatCard } from "@/shared/components/ui/stat-card";

export function En0Tool() {
  const [file, setFile] = useState<File | null>(null);
  const [cliente, setCliente] = useState("");
  const [fecha, setFecha] = useState(new Date().toISOString().split("T")[0]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<EstimationZeroResponse | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file || !cliente || !fecha) {
      toast.error("Por favor completá todos los campos");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("cliente", cliente);
    formData.append("fecha", fecha);

    setLoading(true);
    setResult(null);

    try {
      const res = await contadoresApi.runEstimationZero(formData);
      setResult(res);
      toast.success("Planilla de Estimación en 0 procesada con éxito");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error al procesar la planilla";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader title="Procesamiento de Estimación en 0 (Falta Contador)" icon={FileSpreadsheet} />
        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid gap-5 md:grid-cols-3">
              <FileInput
                id="en0-file"
                label="Archivo CSV / Falta Contador"
                accept=".csv,.txt"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                required
              />
              <Input
                id="en0-cliente"
                label="Nombre del Cliente"
                type="text"
                value={cliente}
                onChange={(e) => setCliente(e.target.value)}
                placeholder="Ej: BANCO DE CORRIENTES"
                required
              />
              <Input
                id="en0-fecha"
                label="Fecha de Lectura"
                type="date"
                value={fecha}
                onChange={(e) => setFecha(e.target.value)}
                required
              />
            </div>

            <Button type="submit" loading={loading}>
              <FileSpreadsheet className="h-4 w-4" />
              Procesar Estimación en 0
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

            <a
              href={contadoresApi.getOutputUrl(result.csv_filename)}
              download={result.csv_filename}
              className={buttonClasses({ variant: "success" })}
            >
              <Download className="h-4 w-4" />
              Descargar Archivo CSV Resultado (.csv)
            </a>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
