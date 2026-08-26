import { test as base, expect } from "@playwright/test";

/** `test` con sesión ya autenticada: el proxy (proxy.ts/middleware) redirige a
 * /login si no hay cookie `hdm_session`, así que se setea acá una sola vez
 * (sobreescribiendo el fixture `context`, del que depende `page`) en vez de
 * repetirlo a mano en cada spec. El valor de la cookie no se valida -- el
 * mock backend (`global-setup.ts`) responde igual a `/api/auth/me` para
 * cualquier contenido. */
export const test = base.extend({
  context: async ({ context }, use) => {
    await context.addCookies([
      {
        name: "hdm_session",
        value: "playwright-test",
        domain: "localhost",
        path: "/",
        httpOnly: true,
        secure: false,
      },
    ]);
    // El callback `use` de un fixture de Playwright no tiene nada que ver con
    // el hook `use()` de React -- eslint-plugin-react-hooks igual lo confunde
    // por el nombre.
    // eslint-disable-next-line react-hooks/rules-of-hooks
    await use(context);
  },
});

export { expect };
