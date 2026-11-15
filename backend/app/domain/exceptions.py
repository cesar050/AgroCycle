class ConflictoEliminacionError(Exception):
    """Se lanza cuando una entidad no puede eliminarse porque tiene
    hijos activos asociados (ej. una finca con lotes activos)."""
    pass
