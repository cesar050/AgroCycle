from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Finca:
    agricultor_id: str
    nombre: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    provincia: Optional[str] = None
    canton: Optional[str] = None
    parroquia: Optional[str] = None
    sector: Optional[str] = None
    descripcion: Optional[str] = None
    geometria_wkt: Optional[str] = None
    superficie_ha: Optional[float] = None
    activo: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def es_del_agricultor(self, agricultor_id: str) -> bool:
        """Verifica que la finca pertenece al agricultor que hace la peticion."""
        return self.agricultor_id == agricultor_id

    def nombre_completo_ubicacion(self) -> str:
        """Retorna la ubicacion completa legible de la finca."""
        partes = [p for p in [self.sector, self.parroquia, self.canton, self.provincia] if p]
        return ", ".join(partes) if partes else "Ubicacion no especificada"
    
    def tiene_geometria(self)-> bool:
        """Verifica si la finca tiene un poligono definido"""
        return self.geometria_wkt is not None