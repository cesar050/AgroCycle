from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
import uuid


@dataclass
class Actividad:
    temporada_id: str
    tipo_actividad_id: int
    fecha: date
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    temporada_parcela_id: Optional[str] = None
    descripcion: Optional[str] = None
    observaciones: Optional[str] = None
    costo_total: float = 0
    registrado_por: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)