from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
import uuid


@dataclass
class EvaluacionCampo:
    """
    Representa una evaluación técnica presencial realizada
    por el agrónomo en la parcela del agricultor.

    Captura datos observacionales directos que las APIs
    climáticas y los registros del agricultor no pueden
    capturar — como la densidad real de plantas establecidas
    o la incidencia visual de estrés nutricional.

    Estos datos enriquecen el modelo predictivo con
    información de campo real.
    """
    agronomo_id: str
    temporada_id: str
    fecha: date

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    temporada_parcela_id: Optional[str] = None
    densidad_plantas_ha: Optional[int] = None
    incidencia_plagas_porcentaje: Optional[float] = None
    incidencia_enfermedades_porcentaje: Optional[float] = None
    estado_nutricional: Optional[str] = None
    estado_fenologico_confirmado: Optional[str] = None
    observaciones: Optional[str] = None
    alerta_generada: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)

    ESTADOS_NUTRICIONALES = {
        'excelente', 'bueno', 'regular', 'deficiente'
    }

    def __post_init__(self):
        """Valida el estado nutricional si fue proporcionado."""
        if (self.estado_nutricional and
                self.estado_nutricional not in self.ESTADOS_NUTRICIONALES):
            raise ValueError(
                f"Estado nutricional '{self.estado_nutricional}' no válido. "
                f"Use: {', '.join(sorted(self.ESTADOS_NUTRICIONALES))}"
            )

    def requiere_alerta(self) -> bool:
        """
        Determina si la evaluación debe generar una alerta al agricultor.
        Se activa si hay incidencia de plagas o enfermedades mayor al 20%
        o si el estado nutricional es deficiente.
        """
        if (self.incidencia_plagas_porcentaje and
                self.incidencia_plagas_porcentaje > 20):
            return True
        if (self.incidencia_enfermedades_porcentaje and
                self.incidencia_enfermedades_porcentaje > 20):
            return True
        if self.estado_nutricional == 'deficiente':
            return True
        return False