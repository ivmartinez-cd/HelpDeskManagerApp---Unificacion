"use client";

import { StickyNote } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { cn } from "@/shared/utils/cn";
import { notaApi } from "../api/nota-api";
import { DashboardCard } from "./dashboard-card";
import { Freshness } from "./dashboard-card-bits";

/** Debounce del autosave: se guarda la nota completa tras una pausa de
 * escritura o al perder el foco — nunca por tecla (bloat MVCC en Postgres,
 * ver docs/MASTER_PROMPT_NOTA_PERSONAL_INICIO.md). */
const DEBOUNCE_MS = 800;
/** Espejo del tope del backend (la fuente de verdad es `MAX_NOTE_CHARS`;
 * el GET lo trae en `maxChars` y lo pisa si cambió). */
const MAX_CHARS_DEFAULT = 4000;

type Estado = "cargando" | "guardado" | "editando" | "guardando" | "error";

const ESTADO_TEXTO: Record<Estado, string> = {
  cargando: "Cargando…",
  guardado: "Guardado",
  editando: "Sin guardar",
  guardando: "Guardando…",
  error: "No se pudo guardar",
};

/** Nota personal (scratchpad) del usuario logueado en Inicio: texto libre
 * que persiste por cuenta. Privada: el backend solo expone la del usuario de
 * la sesión. */
export function NotaPersonalCard() {
  const [texto, setTexto] = useState("");
  const [maxChars, setMaxChars] = useState(MAX_CHARS_DEFAULT);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [estado, setEstado] = useState<Estado>("cargando");
  const [errorCarga, setErrorCarga] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const ultimoGuardado = useRef("");

  useEffect(() => {
    let alive = true;
    notaApi
      .get()
      .then((n) => {
        if (!alive) return;
        ultimoGuardado.current = n.content;
        setTexto(n.content);
        setMaxChars(n.maxChars);
        setUpdatedAt(n.updatedAt);
        setEstado("guardado");
      })
      .catch((err: unknown) => {
        console.error("Error al cargar la nota personal:", err);
        if (alive) setErrorCarga("No se pudo cargar la nota.");
      });
    return () => {
      alive = false;
      if (timer.current) clearTimeout(timer.current);
    };
  }, []);

  const guardar = (contenido: string) => {
    if (contenido === ultimoGuardado.current) {
      setEstado("guardado");
      return;
    }
    setEstado("guardando");
    notaApi
      .put(contenido)
      .then((n) => {
        ultimoGuardado.current = n.content;
        setUpdatedAt(n.updatedAt);
        // Si el usuario siguió escribiendo mientras se guardaba, el debounce
        // pendiente vuelve a guardar; el estado lo refleja.
        setEstado((prev) => (prev === "guardando" ? "guardado" : prev));
      })
      .catch((err: unknown) => {
        console.error("Error al guardar la nota personal:", err);
        setEstado("error");
      });
  };

  const programarGuardado = (contenido: string) => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => guardar(contenido), DEBOUNCE_MS);
  };

  const onChange = (valor: string) => {
    const recortado = valor.slice(0, maxChars);
    setTexto(recortado);
    setEstado("editando");
    programarGuardado(recortado);
  };

  const onBlur = () => {
    if (timer.current) clearTimeout(timer.current);
    guardar(texto);
  };

  return (
    <DashboardCard
      icon={StickyNote}
      title="Mi nota"
      subtitle="Solo la ves vos · se guarda sola"
      error={errorCarga}
      headerRight={
        <span
          className={cn(
            "font-body text-[11px]",
            estado === "error" ? "font-semibold text-destructive" : "text-muted-foreground",
          )}
          aria-live="polite"
        >
          {ESTADO_TEXTO[estado]}
        </span>
      }
      footer={
        <>
          {updatedAt ? (
            <Freshness at={updatedAt} prefix="Guardado" />
          ) : (
            <span className="font-body text-[11px] text-muted-foreground">Todavía sin guardar</span>
          )}
          <span className="font-body text-[11px] text-muted-foreground tabular-nums">
            {texto.length} / {maxChars}
          </span>
        </>
      }
    >
      <textarea
        aria-label="Nota personal"
        value={texto}
        disabled={estado === "cargando"}
        maxLength={maxChars}
        placeholder="Anotá lo que necesites recordar…"
        onChange={(e) => onChange(e.target.value)}
        onBlur={onBlur}
        className="h-full min-h-[96px] w-full flex-1 resize-none rounded-[8px] border border-border bg-surface-2 px-3 py-2 font-body text-[13px] text-foreground outline-none placeholder:text-muted-foreground/70 focus-visible:ring-2 focus-visible:ring-brand-orange/40 disabled:opacity-60"
      />
    </DashboardCard>
  );
}
