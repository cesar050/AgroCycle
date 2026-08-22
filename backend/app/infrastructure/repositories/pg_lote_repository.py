from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_GeomFromText, ST_Contains
from sqlalchemy import text
from app.domain.entities.lote import Lote
from app.domain.repositories.i_lote_repository import ILoteRepository
from app.infrastructure.models.lote_model import LoteModel
import uuid

class PgLoteRepository(ILoteRepository):
    
    def __init__(self, db: Session):
        self.db = db

    def guardar(self, lote: Lote)-> Lote:
        geometria = None
        if lote.geometria_wkt:
            geometria = ST_GeomFromText(lote.geometria_wkt, 4326)

        modelo = LoteModel(
            id=uuid.UUID(lote.id),
            finca_id=uuid.UUID(lote.finca_id),
            nombre=lote.nombre, 
            descripcion=lote.descripcion,
            geometria=geometria,
            superficie_ha=lote.superficie_ha,
            activo=lote.activo
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)
    
    def buscar_por_id(self, lote_id: str) -> Optional[Lote]:
        modelo = self.db.query(LoteModel).filter(
            LoteModel.id == uuid.UUID(lote_id)
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None
    
    def listar_por_finca(self, finca_id:str)-> List[Lote]:
        modelos = self.db.query(LoteModel).filter(
            LoteModel.finca_id == uuid.UUID(finca_id),
            LoteModel.activo == True
        ).order_by(LoteModel.created_at.desc()).all()
        return [self._modelo_a_entidad(m) for m in modelos]
    
    def actualizar(self, lote:Lote)-> Lote:
        modelo = self.db.query(LoteModel).filter(
            LoteModel.id == uuid.UUID(lote.id)
        ).first()
        if not modelo:
            raise ValueError(f"Lote {lote.id} no encontrado")
        if lote.geometria_wkt:
            modelo.geometria = ST_GeomFromText(lote.geometria_wkt, 4326)
        modelo.superficie_ha = lote.superficie_ha
        modelo.nombre = lote.nombre
        modelo.descripcion = lote.descripcion
        modelo.activo = lote.activo
        modelo.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)
    
    def existe_nombre_en_finca(self, nombre:str, finca_id:str)-> bool:
        return self.db.query(LoteModel).filter(
            LoteModel.nombre == nombre,
            LoteModel.finca_id == uuid.UUID(finca_id),
            LoteModel.activo == True
        ).count() > 0
    
    def _modelo_a_entidad(self, modelo: LoteModel)-> Lote:
        return Lote(
            id=str(modelo.id),
            finca_id=str(modelo.finca_id),
            nombre=modelo.nombre,
            descripcion=modelo.descripcion,
            superficie_ha=modelo.superficie_ha,
            geometria_wkt='guardada' if modelo.geometria is not None else None,
            activo=modelo.activo,
            created_at=modelo.created_at,
            updated_at=modelo.updated_at
        )
    
    def calcular_superficie_ha(self, geometria_wkt: str) -> float:
        """Calcula la superficie en hectareas usando PostGIS."""
        resultado = self.db.execute(
            text("""
                SELECT ST_Area(
                    ST_Transform(ST_GeomFromText(:wkt, 4326), 32717)
                ) / 10000 as superficie_ha
            """),
            {"wkt": geometria_wkt}
        ).fetchone()
        return round(float(resultado.superficie_ha), 4)

    def contiene_geometria(self, lote_id: str, geometria_wkt: str) -> bool:
        """
        Verifica que una geometria este contenida dentro del lote.
        Si el lote no tiene geometria retorna True para no bloquear.
        """
        resultado = self.db.execute(
            text("""
                SELECT 
                    CASE 
                        WHEN l.geometria IS NULL THEN true
                        ELSE ST_Intersects(
                            l.geometria,
                            ST_GeomFromText(:wkt, 4326)
                        )
                    END as contenido
                FROM lotes l
                WHERE l.id = :lote_id
            """),
            {"wkt": geometria_wkt, "lote_id": lote_id}
        ).fetchone()
        return bool(resultado.contenido) if resultado else True