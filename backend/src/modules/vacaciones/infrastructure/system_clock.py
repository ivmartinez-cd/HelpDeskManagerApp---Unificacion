from datetime import date


class SystemClock:
    """Fecha local del servidor (TZ America/Argentina configurada en el
    contenedor). Todas las comparaciones "hoy" del módulo pasan por acá."""

    def hoy(self) -> date:
        return date.today()
