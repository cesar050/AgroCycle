from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class Parcela:

    lote_id: str
    nombre: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    #Geometria se guarda como WKT string en el dominio 
    #La conversion a tipo PostGis ocurre en la capa de infraestructura 
    geometria_wkt: Optional[str]= None
    superficie_ha: Optional[str]= None 
    tipo_suelo_id: Optional[str]= None
    pendiente_porcentaje: Optional[float]= None
    altitud_promedio_msnm: Optional[float]= None
    altitud_minima_msnm: Optional[float]= None
    altitud_maxima_msnm: Optional[float]= None
    orientacion: Optional[str]= None
    drenaje: Optional[str]= None
    acceso_riego: bool = False
    tipo_riego: Optional[str]= None
    observaciones: Optional[str]= None
    activo: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def tiene_geometria(self)-> bool:
        """Verifica si la parcela tiene un poligono definido"""
        return self.geometria_wkt is not None   
    
    def es_del_lote(self, lote_id:str)-> bool:
        """Verifica que la parcela pertenece al lote indicado"""
        return self.lote_id == lote_id