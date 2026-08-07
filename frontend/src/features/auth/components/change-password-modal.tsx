"use client";

import { useState, type FormEvent } from "react";
import { Eye, EyeOff } from "lucide-react";
import { Modal } from "@/shared/components/ui/modal";
import { Button } from "@/shared/components/ui/button";
import { PasswordRequirements } from "@/features/auth/components/password-requirements";
import { useChangePassword } from "@/features/auth/hooks/use-change-password";

interface ChangePasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ChangePasswordModal({ isOpen, onClose }: ChangePasswordModalProps) {
  const { changePassword, loading } = useChangePassword();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPasswords, setShowPasswords] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function reset(): void {
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setError(null);
  }

  function handleClose(): void {
    reset();
    onClose();
  }

  async function handleSubmit(event: FormEvent): Promise<void> {
    event.preventDefault();
    setError(null);
    if (newPassword !== confirmPassword) {
      setError("Las contraseñas no coinciden");
      return;
    }
    const result = await changePassword(currentPassword, newPassword);
    if (result.ok) {
      reset();
      onClose();
      return;
    }
    setError(result.message);
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Cambiar contraseña"
      maxWidth="max-w-md"
      error={error}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <PasswordField
          id="current-password"
          label="Contraseña actual"
          value={currentPassword}
          onChange={setCurrentPassword}
          show={showPasswords}
          onToggleShow={() => setShowPasswords((visible) => !visible)}
          autoComplete="current-password"
        />
        <div>
          <PasswordField
            id="new-password"
            label="Nueva contraseña"
            value={newPassword}
            onChange={setNewPassword}
            show={showPasswords}
            onToggleShow={() => setShowPasswords((visible) => !visible)}
            autoComplete="new-password"
          />
          <div className="mt-2">
            <PasswordRequirements password={newPassword} />
          </div>
        </div>
        <PasswordField
          id="confirm-new-password"
          label="Confirmar nueva contraseña"
          value={confirmPassword}
          onChange={setConfirmPassword}
          show={showPasswords}
          onToggleShow={() => setShowPasswords((visible) => !visible)}
          autoComplete="new-password"
        />
        <div className="flex justify-end gap-3 pt-2">
          <Button type="button" variant="outline" onClick={handleClose}>
            Cancelar
          </Button>
          <Button type="submit" loading={loading}>
            Guardar
          </Button>
        </div>
      </form>
    </Modal>
  );
}

interface PasswordFieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  show: boolean;
  onToggleShow: () => void;
  autoComplete: string;
}

function PasswordField({
  id,
  label,
  value,
  onChange,
  show,
  onToggleShow,
  autoComplete,
}: PasswordFieldProps) {
  return (
    <div>
      <label
        htmlFor={id}
        className="mb-1.5 block text-xs font-bold uppercase tracking-wide text-muted-foreground"
      >
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type={show ? "text" : "password"}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="••••••••"
          autoComplete={autoComplete}
          required
          className="w-full rounded-xl border border-black/10 dark:border-white/10 bg-background px-3 py-2 pr-10 text-sm outline-none focus:ring-2 focus:ring-accent/40"
        />
        <button
          type="button"
          onClick={onToggleShow}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          aria-label={show ? "Ocultar contraseña" : "Mostrar contraseña"}
        >
          {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
      </div>
    </div>
  );
}
