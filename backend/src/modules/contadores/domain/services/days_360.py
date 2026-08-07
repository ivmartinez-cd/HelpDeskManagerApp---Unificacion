from datetime import date


def days_360(start: date, end: date) -> int:
    """Convención financiera 30/360: cada mes cuenta 30 días. Puede dar
    negativo si `end` es cronológicamente anterior a `start` — es el
    resultado matemático correcto para ese orden, no un caso a validar acá."""
    d1 = min(30, start.day)
    d2 = end.day
    if d1 == 30 and d2 == 31:
        d2 = 30
    return (end.year - start.year) * 360 + (end.month - start.month) * 30 + (d2 - d1)
