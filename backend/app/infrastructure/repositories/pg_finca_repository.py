"""
Implementacion PostgreSQL del repositorio de Finca.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_GeomFromText
from sqlalchemy import text
from app.domain.entities.finca import Finca
from app.domain.repositories.i_finca_repository import IFincaRepository
from app.infrastructure.models.finca_model import FincaModel
import uuid


class PgFincaRepository(IFincaRepository):

    def __init__(self, db: Session):
        self.db = db

    def guardar(self, finca: Finca) -> Finca:
        geometria = None
        if finca.geometria_wkt:
            geometria = ST_GeomFromText(finca.geometria_wkt, 4326)
        modelo = FincaModel(
            id=uuid.UUID(finca.id),
            agricultor_id=uuid.UUID(finca.agricultor_id),
            nombre=finca.nombre,
            provincia=finca.provincia,
            canton=finca.canton,
            parroquia=finca.parroquia,
            sector=finca.sector,
            descripcion=finca.descripcion,
            geometria=geometria,
            superficie_ha=finca.superficie_ha,
            activo=finca.activo
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)

    def buscar_por_id(self, finca_id: str) -> Optional[Finca]:
        modelo = self.db.query(FincaModel).filter(
            FincaModel.id == uuid.UUID(finca_id)
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    def listar_por_agricultor(self, agricultor_id: str) -> List[Finca]:
        modelos = self.db.query(FincaModel).filter(
            FincaModel.agricultor_id == uuid.UUID(agricultor_id),
            FincaModel.activo == True
        ).order_by(FincaModel.created_at.desc()).all()
        return [self._modelo_a_entidad(m) for m in modelos]

    def actualizar(self, finca: Finca) -> Finca:
        modelo = self.db.query(FincaModel).filter(
            FincaModel.id == uuid.UUID(finca.id)
        ).first()
        if not modelo:
            raise ValueError(f"Finca {finca.id} no encontrada")
        if finca.geometria_wkt and finca.geometria_wkt != 'guardada':
            modelo.geometria = ST_GeomFromText(finca.geometria_wkt, 4326)
        modelo.superficie_ha = finca.superficie_ha
        modelo.nombre = finca.nombre
        modelo.provincia = finca.provincia
        modelo.canton = finca.canton
        modelo.parroquia = finca.parroquia
        modelo.sector = finca.sector
        modelo.descripcion = finca.descripcion
        modelo.activo = finca.activo
        modelo.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)

    def existe_nombre_para_agricultor(self, nombre: str, agricultor_id: str) -> bool:
        return self.db.query(FincaModel).filter(
            FincaModel.nombre == nombre,
            FincaModel.agricultor_id == uuid.UUID(agricultor_id),
            FincaModel.activo == True
        ).count() > 0

    def calcular_superficie_ha(self, geometria_wkt: str) -> float:
        resultado = self.db.execute(
            text("""
                SELECT ST_Area(
                    ST_Transform(ST_GeomFromText(:wkt, 4326), 32717)
                ) / 10000 as superficie_ha
            """),
            {"wkt": geometria_wkt}
        ).fetchone()
        return round(float(resultado.superficie_ha), 4)

    def contiene_geometria(self, finca_id: str, geometria_wkt: str) -> bool:
        """
        Verifica que una geometria este contenida dentro de la finca.
        Si la finca no tiene geometria retorna True para no bloquear.
        """
        resultado = self.db.execute(
            text("""
                SELECT
                    CASE
                        WHEN f.geometria IS NULL THEN true
                    ELSE ST_Intersects(
                        f.geometria,
                        ST_GeomFromText(:wkt, 4326)
                    )
                    END as contenido
                FROM fincas f
                WHERE f.id = CAST(:finca_id AS uuid)
            """),
            {"wkt": geometria_wkt, "finca_id": finca_id}
        ).fetchone()
        return bool(resultado.contenido) if resultado else True

    def _modelo_a_entidad(self, modelo: FincaModel) -> Finca:
        return Finca(
            id=str(modelo.id),
            agricultor_id=str(modelo.agricultor_id),
            nombre=modelo.nombre,
            provincia=modelo.provincia,
            canton=modelo.canton,
            parroquia=modelo.parroquia,
            sector=modelo.sector,
            descripcion=modelo.descripcion,
            superficie_ha=modelo.superficie_ha,
            geometria_wkt='guardada' if modelo.geometria is not None else None,
            activo=modelo.activo,
            created_at=modelo.created_at,
            updated_at=modelo.updated_at
        )