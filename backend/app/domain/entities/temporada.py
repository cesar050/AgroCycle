from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
import uuid

@dataclass
class Temporada:
    agricultor_id: str
    finca_id: str
    cultivo_id: int
    nombre: str
    fecha_inicio: date
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fecha_fin_estimada: Optional[date] = None
    fecha_fin_real: Optional[date] = None
    estado: str = 'activa'
    observaciones: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def esta_activa(self) -> bool:
        """Verifica si la temporada esta en curso."""
        return self.estado == 'activa'
    
    def puede_cerrar(self)-> bool:
        """
        Una temporada solo puede cerrar si esta activa.
        No se puede cerrar una temporada ya cerrada o cancelada
        """
        return self.estado == 'activa'
    
    def es_del_agricultor(self, agricultor_id:str)-> bool:
        """Verifica que la temporada pertenece al agricultor"""
        return self.agricultor_id == agricultor_id


    