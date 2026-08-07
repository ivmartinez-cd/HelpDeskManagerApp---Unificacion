"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { Eye, EyeOff } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { AuthSplitLayout } from "@/features/auth/components/auth-split-layout";
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
    <AuthSplitLayout>
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
          <div className="mb-1.5 flex items-center justify-between">
            <label
              htmlFor="login-password"
              className="block text-xs font-bold uppercase tracking-wide text-muted-foreground"
            >
              Contraseña
            </label>
            <Link
              href="/forgot-password"
              className="text-xs font-medium text-accent hover:underline"
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
    </AuthSplitLayout>
  );
}
