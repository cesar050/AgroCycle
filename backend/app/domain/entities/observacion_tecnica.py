from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
import uuid


@dataclass
class ObservacionTecnica:
    """
    Representa una observación técnica registrada por el agrónomo
    sobre el estado de un cultivo, suelo o condiciones generales
    de una parcela durante una temporada activa.

    Una observación puede ser general para toda la temporada
    (temporada_parcela_id = None) o específica para una parcela.
    """
    agronomo_id: str
    temporada_id: str
    tipo: str
    descripcion: str
    fecha: date

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    temporada_parcela_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Tipos válidos de observación
    TIPOS_VALIDOS = {'cultivo', 'suelo', 'condiciones_generales'}

    def __post_init__(self):
        """Valida que el tipo sea uno de los permitidos."""
        if self.tipo not in self.TIPOS_VALIDOS:
            raise ValueError(
                f"Tipo '{self.tipo}' no válido. "
                f"Use: {', '.join(sorted(self.TIPOS_VALIDOS))}"
            )

    def es_general(self) -> bool:
        """
        Retorna True si la observación aplica a toda la temporada
        y no a una parcela específica.
        """
        return self.temporada_parcela_id is None