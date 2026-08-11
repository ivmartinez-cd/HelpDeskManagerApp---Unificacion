"""Detección de solicitudes "stale": el cartucho ya fue reemplazado físicamente pero
HP SDS no cerró el workflowStatus OUTSTANDING (port de api_helpers.is_stale_replaced)."""


def is_stale_replaced(requested: str | None, replaced_date: str | None) -> bool:
    """True si `replacedDate` es posterior a `requested`.

    Ambos campos son ISO-Z UTC verificado de Insight (caracterización §7) — la
    comparación lexicográfica de los strings crudos es correcta y es exactamente lo
    que hacía el legacy; no parsear acá.
    """
    return bool(replaced_date) and bool(requested) and str(replaced_date) > str(requested)
