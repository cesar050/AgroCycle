class ConflictoEliminacionError(Exception):
    """Se lanza cuando una entidad no puede eliminarse porque tiene
    hijos activos asociados (ej. una finca con lotes activos)."""
    pass


class ValorInvalidoError(Exception):
    """Se lanza cuando un campo no cumple una regla de dominio con un
    conjunto fijo de valores validos (ej. drenaje, tipo_riego). Se
    distingue deliberadamente de ValueError —ya usado en el codebase
    para "entidad no encontrada"— para que las rutas puedan mapearlo
    siempre a 400 sin heredar el 404/409 que algunas rutas le dan a
    ValueError."""
    pass
