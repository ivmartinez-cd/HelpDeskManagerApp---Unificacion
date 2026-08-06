"use client";

import { useState, type FormEvent } from "react";
import { Eye, EyeOff } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { HelpDeskLogo } from "@/shared/components/helpdesk-logo";
import { Input } from "@/shared/components/ui/input";
import { useLogin } from "@/features/auth/hooks/use-login";

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
    <div className="flex min-h-screen">
      {/* Panel izquierdo: identidad de marca — oculto en pantallas chicas */}
      <div className="hidden lg:flex lg:w-1/2 flex-col items-center justify-center bg-[#1a1a1a] px-12 relative overflow-hidden">
        {/* eslint-disable-next-line @next/next/no-img-element -- SVG, next/image no aporta acá */}
        <img
          src="/isotipo.svg"
          alt=""
          aria-hidden="true"
          className="absolute -bottom-16 -right-16 h-80 w-80 opacity-5 select-none pointer-events-none"
        />
        <div className="relative z-10 flex flex-col items-center text-center max-w-sm">
          <HelpDeskLogo size="lg" className="mb-8" />
          <div className="w-12 h-0.5 bg-accent mb-8 rounded-full" />
          {/* eslint-disable-next-line @next/next/no-img-element -- SVG */}
          <img src="/logo-white.svg" alt="Canal Directo" className="h-8 w-auto mb-8 opacity-70" />
          <h1 className="text-2xl font-bold text-white leading-snug">
            Plataforma Unificada
            <br />
            de Operaciones
          </h1>
          <p className="mt-4 text-sm text-white/50 leading-relaxed">
            Insumos, liquidaciones, vacaciones, parque de impresoras y monitoreo, todo en un
            solo lugar.
          </p>
        </div>
      </div>

      {/* Panel derecho: formulario */}
      <div className="flex flex-1 items-center justify-center bg-background px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex flex-col items-center lg:hidden">
            {/* eslint-disable-next-line @next/next/no-img-element -- SVG */}
            <img src="/logo.svg" alt="HelpDesk Manager" className="h-10 w-auto" />
          </div>
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-foreground">Iniciar sesión</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Ingresá con tus credenciales corporativas
            </p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              id="email"
              label="Email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="tu.nombre@empresa.com"
              autoComplete="username"
              required
            />
            <div>
              <label
                htmlFor="login-password"
                className="mb-1.5 block text-xs font-bold uppercase tracking-wide text-muted-foreground"
              >
                Contraseña
              </label>
              <div className="relative">
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  required
                  className="w-full rounded-xl border border-black/10 dark:border-white/10 bg-background px-3 py-2 pr-10 text-sm outline-none focus:ring-2 focus:ring-accent/40"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((visible) => !visible)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            <Button type="submit" loading={loading} className="w-full">
              Ingresar
            </Button>
          </form>
          <p className="mt-8 text-center text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} HelpDesk Manager. Uso interno.
          </p>
        </div>
      </div>
    </div>
  );
}
