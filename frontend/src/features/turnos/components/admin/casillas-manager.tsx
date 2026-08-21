"use client";

import { CalendarClock, Edit2, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { turnosApi } from "../../api/turnos-api";
import type { Casilla, Slot, UserOption } from "../../types/turnos";
import { Button } from "@/shared/components/ui/button";
import { Spinner } from "@/shared/components/ui/spinner";
import { useSession } from "@/services/session-provider";
import { CasillaFormModal } from "./casilla-form-modal";
import { SlotFormModal } from "./slot-form-modal";
import { SlotsTable } from "./slots-table";

export function CasillasManager() {
  // turnos.view abre la grilla; toda mutación (casillas, franjas, asignaciones)
  // es turnos.manage (ADR-029) — los botones se ocultan, el backend igual corta.
  const { can } = useSession();
  const puedeEditar = can("turnos", "manage");
  const [casillas, setCasillas] = useState<Casilla[]>([]);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [selectedCasillaId, setSelectedCasillaId] = useState<string | null>(null);
  const [selectedDia, setSelectedDia] = useState<number>(0); // 0=Lunes
  const [loading, setLoading] = useState(true);

  // Modal Casilla
  const [casillaModalOpen, setCasillaModalOpen] = useState(false);
  const [editingCasilla, setEditingCasilla] = useState<Casilla | null>(null);
  const [casillaNombre, setCasillaNombre] = useState("");

  // Modal Slot
  const [slotModalOpen, setSlotModalOpen] = useState(false);
  const [editingSlot, setEditingSlot] = useState<Slot | null>(null);
  const [horaInicio, setHoraInicio] = useState("08:00");
  const [horaFin, setHoraFin] = useState("11:00");
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [cList, sList, uList] = await Promise.all([
        turnosApi.listCasillas(),
        turnosApi.listSlots(),
        turnosApi.listAssignableUsers(),
      ]);
      setCasillas(cList);
      setSlots(sList);
      setUsers(uList);
      // Forma funcional: si ya hay una casilla seleccionada, la conserva;
      // si no, auto-selecciona la primera. No cierra sobre selectedCasillaId.
      setSelectedCasillaId((prev) => prev ?? (cList[0]?.id ?? null));
    } catch (err) {
      console.error("Error al cargar datos de turnos:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadData();
  }, [loadData]);

  const handleSaveCasilla = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!casillaNombre.trim()) return;
    try {
      if (editingCasilla) {
        await turnosApi.updateCasilla(editingCasilla.id, { nombre: casillaNombre });
      } else {
        await turnosApi.createCasilla({ nombre: casillaNombre });
      }
      setCasillaModalOpen(false);
      setCasillaNombre("");
      setEditingCasilla(null);
      await loadData();
    } catch (err) {
      console.error("Error al guardar casilla:", err);
    }
  };

  const handleDeleteCasilla = async (id: string) => {
    if (!confirm("¿Eliminar esta casilla y sus franjas horarias?")) return;
    try {
      await turnosApi.deleteCasilla(id);
      if (selectedCasillaId === id) setSelectedCasillaId(null);
      await loadData();
    } catch (err) {
      console.error("Error al eliminar casilla:", err);
    }
  };

  const handleOpenSlotModal = (slot?: Slot) => {
    if (slot) {
      setEditingSlot(slot);
      setHoraInicio(slot.horaInicio.slice(0, 5));
      setHoraFin(slot.horaFin.slice(0, 5));
      setSelectedUserIds(Array.from(new Set(slot.asignaciones.map((a) => a.userId))));
    } else {
      setEditingSlot(null);
      setHoraInicio("08:00");
      setHoraFin("11:00");
      setSelectedUserIds([]);
    }
    setSlotModalOpen(true);
  };

  const handleSaveSlot = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCasillaId) return;
    try {
      let slotId = editingSlot?.id;
      if (editingSlot) {
        await turnosApi.updateSlot(editingSlot.id, {
          casillaId: selectedCasillaId,
          horaInicio,
          horaFin,
          diaSemana: selectedDia,
        });
      } else {
        const created = await turnosApi.createSlot({
          casillaId: selectedCasillaId,
          horaInicio,
          horaFin,
          diaSemana: selectedDia,
        });
        slotId = created.id;
      }

      if (slotId) {
        const todayStr = new Date().toISOString().slice(0, 10);
        await turnosApi.replaceAssignments(slotId, selectedUserIds, todayStr);
      }

      setSlotModalOpen(false);
      await loadData();
    } catch (err) {
      console.error("Error al guardar slot:", err);
    }
  };

  const handleDeleteSlot = async (id: string) => {
    if (!confirm("¿Eliminar esta franja horaria?")) return;
    try {
      await turnosApi.deleteSlot(id);
      await loadData();
    } catch (err) {
      console.error("Error al eliminar slot:", err);
    }
  };

  if (loading && casillas.length === 0) {
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    );
  }

  const activeSlots = slots.filter(
    (s) => s.casillaId === selectedCasillaId && s.diaSemana === selectedDia
  );

  return (
    <div className="flex flex-col gap-6">
      {/* Selector de Casillas y botón de crear */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
        <div className="flex flex-wrap items-center gap-2">
          {casillas.map((c) => (
            <div key={c.id} className="flex items-center gap-1">
              <button
                onClick={() => setSelectedCasillaId(c.id)}
                className={`rounded-[8px] px-3.5 py-2 font-heading text-xs font-bold transition-colors ${
                  selectedCasillaId === c.id
                    ? "bg-brand-orange text-white"
                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                }`}
              >
                {c.nombre}
              </button>
              {puedeEditar && (
                <>
                  <button
                    onClick={() => {
                      setEditingCasilla(c);
                      setCasillaNombre(c.nombre);
                      setCasillaModalOpen(true);
                    }}
                    className="p-1 text-muted-foreground hover:text-foreground"
                    title="Editar nombre de casilla"
                  >
                    <Edit2 className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => handleDeleteCasilla(c.id)}
                    className="p-1 text-muted-foreground hover:text-destructive"
                    title="Eliminar casilla"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </>
              )}
            </div>
          ))}
          {casillas.length === 0 && (
            <span className="font-body text-xs text-muted-foreground">
              No hay casillas creadas.
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Link href="/turnos/coberturas">
            <Button variant="outline" size="sm" className="gap-1.5">
              <CalendarClock className="h-4 w-4" />
              Coberturas
            </Button>
          </Link>
          {puedeEditar && (
            <Button
              onClick={() => {
                setEditingCasilla(null);
                setCasillaNombre("");
                setCasillaModalOpen(true);
              }}
              size="sm"
              className="gap-1.5"
            >
              <Plus className="h-4 w-4" />
              Nueva Casilla
            </Button>
          )}
        </div>
      </div>

      {selectedCasillaId && (
        <SlotsTable
          selectedDia={selectedDia}
          setSelectedDia={setSelectedDia}
          activeSlots={activeSlots}
          puedeEditar={puedeEditar}
          onAddSlot={() => handleOpenSlotModal()}
          onEditSlot={handleOpenSlotModal}
          onDeleteSlot={handleDeleteSlot}
        />
      )}

      <CasillaFormModal
        isOpen={casillaModalOpen}
        isEditing={editingCasilla !== null}
        nombre={casillaNombre}
        setNombre={setCasillaNombre}
        onClose={() => setCasillaModalOpen(false)}
        onSubmit={handleSaveCasilla}
      />

      <SlotFormModal
        isOpen={slotModalOpen}
        isEditing={editingSlot !== null}
        horaInicio={horaInicio}
        setHoraInicio={setHoraInicio}
        horaFin={horaFin}
        setHoraFin={setHoraFin}
        users={users}
        selectedUserIds={selectedUserIds}
        setSelectedUserIds={setSelectedUserIds}
        onClose={() => setSlotModalOpen(false)}
        onSubmit={handleSaveSlot}
      />
    </div>
  );
}
