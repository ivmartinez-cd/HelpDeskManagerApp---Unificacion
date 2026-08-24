"use client";

import { useEffect, useRef, useState } from "react";

/** Si el body con scroll de una card deja contenido cortado abajo — para
 * mostrar un fade en el borde en vez de un renglón partido a la mitad sin
 * aviso (`mask-fade-bottom` en globals.css). Recalcula en scroll/resize y
 * cuando cambia el contenido (ResizeObserver, se dispara al crecer la lista
 * sin que el contenedor cambie de tamaño). */
export function useScrollShadow<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [bottom, setBottom] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const check = () => setBottom(el.scrollHeight - el.scrollTop - el.clientHeight > 1);
    check();
    el.addEventListener("scroll", check, { passive: true });
    const ro = new ResizeObserver(check);
    ro.observe(el);
    return () => {
      el.removeEventListener("scroll", check);
      ro.disconnect();
    };
  }, []);

  return { ref, bottom };
}
