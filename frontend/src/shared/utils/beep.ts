/** Aviso sonoro corto (dos tonos) con Web Audio, sin assets. Los navegadores
 * bloquean el audio hasta la primera interacción del usuario con la pestaña:
 * si el contexto no se puede arrancar, falla en silencio (el toast igual se
 * muestra). */

let ctx: AudioContext | null = null;

function getContext(): AudioContext | null {
  if (typeof window === "undefined") return null;
  try {
    ctx ??= new AudioContext();
    return ctx;
  } catch {
    return null;
  }
}

function tono(audio: AudioContext, inicio: number, freq: number, dur: number): void {
  const osc = audio.createOscillator();
  const gain = audio.createGain();
  osc.type = "sine";
  osc.frequency.value = freq;
  gain.gain.setValueAtTime(0.0001, inicio);
  gain.gain.exponentialRampToValueAtTime(0.25, inicio + 0.02);
  gain.gain.exponentialRampToValueAtTime(0.0001, inicio + dur);
  osc.connect(gain).connect(audio.destination);
  osc.start(inicio);
  osc.stop(inicio + dur + 0.05);
}

export function sonarAviso(): void {
  const audio = getContext();
  if (!audio) return;
  const reproducir = () => {
    const t = audio.currentTime;
    tono(audio, t, 880, 0.18);
    tono(audio, t + 0.22, 1175, 0.22);
  };
  if (audio.state === "suspended") {
    audio.resume().then(reproducir).catch(() => {
      // Sin gesto previo del usuario el navegador no deja sonar: se omite.
    });
    return;
  }
  reproducir();
}
