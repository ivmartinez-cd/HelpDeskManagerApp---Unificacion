"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { AuthSplitLayout } from "@/features/auth/components/auth-split-layout";
import { useLogin } from "@/features/auth/hooks/use-login";

const fieldLabelClass = "font-body text-[13px] font-semibold text-[#4b4b4b]";
const fieldInputClass =
  "w-full rounded-[8px] border border-black/15 bg-white px-[14px] py-[11px] font-body text-sm text-brand-charcoal outline-none transition-shadow focus:ring-2 focus:ring-brand-orange/40";

export function LoginForm() {
  const { login, loading } = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  async function handleSubmit(event: FormEvent): Promise<void> {
    event.preventDefault();
    await login(email, password);
  }

  return (
    <AuthSplitLayout>
      <div className="mb-[26px] flex flex-col gap-1.5">
        <h2 className="font-heading text-[25px] font-extrabold text-brand-charcoal">
          Iniciar sesión
        </h2>
        <p className="font-body text-sm text-[#8a8a8a]">
          Ingresá con tus credenciales corporativas
        </p>
      </div>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <label htmlFor="login-email" className={fieldLabelClass}>
            Usuario
          </label>
          <input
            id="login-email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="nombre.apellido@canaldirecto.com.ar"
            autoComplete="username"
            required
            className={fieldInputClass}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <label htmlFor="login-password" className={fieldLabelClass}>
              Contraseña
            </label>
            <Link
              href="/forgot-password"
              className="font-body text-[13px] font-semibold text-brand-orange no-underline hover:text-brand-orange-hover"
            >
              ¿Olvidaste tu contraseña?
            </Link>
          </div>
          <div className="relative">
            <input
              id="login-password"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              required
              className={`${fieldInputClass} pr-10`}
            />
            <button
              type="button"
              onClick={() => setShowPassword((visible) => !visible)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[#8a8a8a] hover:text-brand-charcoal"
              aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>
        <label className="flex items-center gap-2 font-body text-[13px] text-[#6b6b6b]">
          <input type="checkbox" className="accent-brand-orange" />
          Recordarme
        </label>
        <button
          type="submit"
          disabled={loading}
          className="mt-1.5 flex items-center justify-center gap-2 rounded-[8px] bg-brand-orange px-[18px] py-3 font-body text-sm font-bold text-white transition-colors hover:bg-brand-orange-hover disabled:opacity-50"
        >
          {loading && <Loader2 className="h-4 w-4 animate-spin" />}
          Ingresar
        </button>
      </form>
    </AuthSplitLayout>
  );
}
