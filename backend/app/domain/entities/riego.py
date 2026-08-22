from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Riego:
    actividad_id: str
    tipo_riego: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    duracion_horas: Optional[float] = None
    porcentaje_parcela_regada: float = 100
    aporte_hidrico_estimado_mm: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)