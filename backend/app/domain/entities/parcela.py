import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

from app.domain.exceptions import ValorInvalidoError


def _normalizar_texto(valor: str) -> str:
    """minusculas + sin tildes/diacriticos (ej. 'Aspersión' -> 'aspersion')."""
    sin_tildes = unicodedata.normalize('NFD', valor)
    sin_tildes = ''.join(c for c in sin_tildes if unicodedata.category(c) != 'Mn')
    return sin_tildes.strip().lower()


@dataclass
class Parcela:

    # Valores exactos permitidos por los CHECK constraints de la tabla
    # "parcelas" en PostgreSQL (parcelas_drenaje_check / parcelas_tipo_riego_check).
    # No estan declarados en los modelos SQLAlchemy ni en ninguna
    # migracion versionada — viven unicamente en el esquema real de la
    # base de datos. Si cambian ahi, deben actualizarse aqui tambien.
    DRENAJE_VALIDOS = {'rapido', 'moderado', 'lento', 'muy_lento'}
    TIPO_RIEGO_VALIDOS = {'perdido', 'aspersion', 'goteo', 'ninguno'}

    lote_id: str
    nombre: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    #Geometria se guarda como WKT string en el dominio
    #La conversion a tipo PostGis ocurre en la capa de infraestructura
    geometria_wkt: Optional[str]= None
    superficie_ha: Optional[float]= None
    tipo_suelo_id: Optional[int]= None
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

    def __post_init__(self):
        self.drenaje = Parcela.normalizar_drenaje(self.drenaje)
        self.tipo_riego = Parcela.normalizar_tipo_riego(self.tipo_riego)

    @staticmethod
    def normalizar_drenaje(valor: Optional[str]) -> Optional[str]:
        if valor is None or valor == '':
            return None
        normalizado = _normalizar_texto(valor)
        if normalizado not in Parcela.DRENAJE_VALIDOS:
            raise ValorInvalidoError(
                f"Drenaje invalido: '{valor}'. Valores permitidos: "
                f"{', '.join(sorted(Parcela.DRENAJE_VALIDOS))}"
            )
        return normalizado

    @staticmethod
    def normalizar_tipo_riego(valor: Optional[str]) -> Optional[str]:
        if valor is None or valor == '':
            return None
        normalizado = _normalizar_texto(valor)
        if normalizado not in Parcela.TIPO_RIEGO_VALIDOS:
            raise ValorInvalidoError(
                f"Tipo de riego invalido: '{valor}'. Valores permitidos: "
                f"{', '.join(sorted(Parcela.TIPO_RIEGO_VALIDOS))}"
            )
        return normalizado

    def tiene_geometria(self)-> bool:
        """Verifica si la parcela tiene un poligono definido"""
        return self.geometria_wkt is not None

    def es_del_lote(self, lote_id:str)-> bool:
        """Verifica que la parcela pertenece al lote indicado"""
        return self.lote_id == lote_id