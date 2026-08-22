from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class Lote:
    finca_id: str
    nombre: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    descripcion: Optional[str] = None
    geometria_wkt: Optional[str]= None
    superficie_ha: Optional[float] = None
    activo: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def es_de_la_finca(self, finca_id:str)-> bool:
        """Verifica que el lote pertenece a la finca indicada"""
        return self.finca_id == finca_id
    
    def tiene_geometria(self)-> bool:
        """Verifica si el lote tiene un poligono definido"""
        return self.geometria_wkt is not None