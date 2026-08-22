from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
import uuid


@dataclass
class RecomendacionAgronomica:
    """
    Representa una recomendación técnica que el agrónomo
    envía al agricultor durante la temporada.

    Tiene nivel de urgencia porque algunas recomendaciones
    requieren acción inmediata — por ejemplo detectar una
    plaga en etapa de floración no puede esperar tres días.
    """
    agronomo_id: str
    temporada_id: str
    descripcion: str
    urgencia: str
    fecha: date

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tipo: Optional[str] = None
    temporada_parcela_id: Optional[str] = None
    fecha_limite: Optional[date] = None
    leida: bool = False
    implementada: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    URGENCIAS_VALIDAS = {'alta', 'media', 'baja'}

    def __post_init__(self):
        """Valida que la urgencia sea válida."""
        if self.urgencia not in self.URGENCIAS_VALIDAS:
            raise ValueError(
                f"Urgencia '{self.urgencia}' no válida. "
                f"Use: {', '.join(sorted(self.URGENCIAS_VALIDAS))}"
            )

    def es_urgente(self) -> bool:
        """Retorna True si requiere atención inmediata."""
        return self.urgencia == 'alta'

    def marcar_leida(self) -> None:
        """El agricultor marcó la recomendación como leída."""
        self.leida = True
        self.updated_at = datetime.utcnow()

    def marcar_implementada(self) -> None:
        """El agricultor implementó la recomendación."""
        self.implementada = True
        self.updated_at = datetime.utcnow()