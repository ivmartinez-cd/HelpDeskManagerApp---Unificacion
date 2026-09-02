"use client";

import * as React from "react";

export type Theme = "light" | "dark";

const STORAGE_KEY = "theme";
const DEFAULT_THEME: Theme = "dark";

type ThemeContextValue = {
  theme: Theme;
  resolvedTheme: Theme;
  setTheme: (theme: Theme) => void;
};

const ThemeContext = React.createContext<ThemeContextValue | undefined>(undefined);

const SET_THEME_CLASS_SCRIPT = `(function(){try{var t=localStorage.getItem("${STORAGE_KEY}");document.documentElement.classList.add(t==="light"?"light":"dark")}catch(e){document.documentElement.classList.add("dark")}})()`;

// Client Component a propósito: React (16.3) marca como error cualquier
// <script> renderizado por un Server Component al hidratar en el cliente
// ("Encountered a script tag while rendering React component"). El truco de
// alternar type server/cliente hace que en el cliente el tag quede inerte
// (text/plain) y no dispare ese chequeo, mientras que en el server sigue
// siendo un <script> real que el browser ejecuta al parsear el HTML, antes
// del primer paint. Ver node_modules/next/dist/docs/01-app/02-guides/
// preventing-flash-before-hydration.md.
export function ThemeScript() {
  return (
    <script
      type={typeof window === "undefined" ? "text/javascript" : "text/plain"}
      suppressHydrationWarning
      dangerouslySetInnerHTML={{ __html: SET_THEME_CLASS_SCRIPT }}
    />
  );
}

export function useTheme() {
  const ctx = React.useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme debe usarse dentro de <ThemeProvider>");
  }
  return ctx;
}

function applyTheme(theme: Theme) {
  document.documentElement.classList.remove("light", "dark");
  document.documentElement.classList.add(theme);
}

function disableTransitionsMomentarily() {
  const style = document.createElement("style");
  style.textContent = "*,*::before,*::after{transition:none!important}";
  document.head.appendChild(style);
  return () => {
    // Fuerza reflow antes de sacar el estilo para que el corte aplique en este frame.
    void window.getComputedStyle(document.body).transition;
    setTimeout(() => document.head.removeChild(style), 1);
  };
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = React.useState<Theme>(() => {
    if (typeof window === "undefined") return DEFAULT_THEME;
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored === "light" || stored === "dark" ? stored : DEFAULT_THEME;
  });

  const setTheme = React.useCallback((next: Theme) => {
    const restore = disableTransitionsMomentarily();
    setThemeState(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // localStorage no disponible (modo privado, cuota llena): el tema queda solo en memoria.
    }
    applyTheme(next);
    restore();
  }, []);

  // El remount de Strict Mode en dev limpia las clases que puso el script
  // inline antes de hidratar; hay que reaplicarlas.
  React.useLayoutEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const value = React.useMemo<ThemeContextValue>(
    () => ({ theme, resolvedTheme: theme, setTheme }),
    [theme, setTheme],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
