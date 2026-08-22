from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from geoalchemy2.functions import ST_Area, ST_Transform, ST_GeomFromText
from app.domain.entities.parcela import Parcela
from app.domain.repositories.i_parcela_repository import IParcelaRepository
from app.infrastructure.models.parcela_model import ParcelaModel
import uuid


class PgParcelaRepository(IParcelaRepository):

    def __init__(self, db: Session):
        self.db = db

    def guardar(self, parcela: Parcela) -> Parcela:
        """
        Guarda la parcela convirtiendo el WKT a geometria PostGIS.
        ST_GeomFromText convierte el string WKT al tipo geometry de PostGIS.
        El 4326 indica que las coordenadas son WGS84 (GPS estandar).
        """
        geometria = None
        if parcela.geometria_wkt:
            geometria = ST_GeomFromText(parcela.geometria_wkt, 4326)

        modelo = ParcelaModel(
            id=uuid.UUID(parcela.id),
            lote_id=uuid.UUID(parcela.lote_id),
            nombre=parcela.nombre,
            geometria=geometria,
            superficie_ha=parcela.superficie_ha,
            tipo_suelo_id=parcela.tipo_suelo_id,
            pendiente_porcentaje=parcela.pendiente_porcentaje,
            altitud_promedio_msnm=parcela.altitud_promedio_msnm,
            altitud_minima_msnm=parcela.altitud_minima_msnm,
            altitud_maxima_msnm=parcela.altitud_maxima_msnm,
            orientacion=parcela.orientacion,
            drenaje=parcela.drenaje,
            acceso_riego=parcela.acceso_riego,
            tipo_riego=parcela.tipo_riego,
            observaciones=parcela.observaciones,
            activo=parcela.activo
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)

    def buscar_por_id(self, parcela_id: str) -> Optional[Parcela]:
        modelo = self.db.query(ParcelaModel).filter(
            ParcelaModel.id == uuid.UUID(parcela_id)
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    def listar_por_lote(self, lote_id: str) -> List[Parcela]:
        modelos = self.db.query(ParcelaModel).filter(
            ParcelaModel.lote_id == uuid.UUID(lote_id),
            ParcelaModel.activo == True
        ).order_by(ParcelaModel.created_at.desc()).all()
        return [self._modelo_a_entidad(m) for m in modelos]

    def actualizar(self, parcela: Parcela) -> Parcela:
        modelo = self.db.query(ParcelaModel).filter(
            ParcelaModel.id == uuid.UUID(parcela.id)
        ).first()
        if not modelo:
            raise ValueError(f"Parcela {parcela.id} no encontrada")

        if parcela.geometria_wkt:
            modelo.geometria = ST_GeomFromText(parcela.geometria_wkt, 4326)

        modelo.nombre = parcela.nombre
        modelo.superficie_ha = parcela.superficie_ha
        modelo.tipo_suelo_id = parcela.tipo_suelo_id
        modelo.pendiente_porcentaje = parcela.pendiente_porcentaje
        modelo.altitud_promedio_msnm = parcela.altitud_promedio_msnm
        modelo.altitud_minima_msnm = parcela.altitud_minima_msnm
        modelo.altitud_maxima_msnm = parcela.altitud_maxima_msnm
        modelo.orientacion = parcela.orientacion
        modelo.drenaje = parcela.drenaje
        modelo.acceso_riego = parcela.acceso_riego
        modelo.tipo_riego = parcela.tipo_riego
        modelo.observaciones = parcela.observaciones
        modelo.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)

    def calcular_superficie_ha(self, geometria_wkt: str) -> float:
        """
        Usa PostGIS para calcular la superficie real del poligono en hectareas.
        ST_Transform(geom, 32717) convierte de WGS84 a UTM zona 17S
        que es el sistema metrico correcto para el sur del Ecuador.
        ST_Area retorna el area en metros cuadrados.
        Dividimos entre 10000 para convertir m2 a hectareas.
        """
        resultado = self.db.execute(
            text("""
                SELECT ST_Area(
                    ST_Transform(
                        ST_GeomFromText(:wkt, 4326),
                        32717
                    )
                ) / 10000 as superficie_ha
            """),
            {"wkt": geometria_wkt}
        ).fetchone()
        return round(float(resultado.superficie_ha), 4)

    def _modelo_a_entidad(self, modelo: ParcelaModel) -> Parcela:
        return Parcela(
            id=str(modelo.id),
            lote_id=str(modelo.lote_id),
            nombre=modelo.nombre,
            geometria_wkt=None,
            superficie_ha=modelo.superficie_ha,
            tipo_suelo_id=modelo.tipo_suelo_id,
            pendiente_porcentaje=modelo.pendiente_porcentaje,
            altitud_promedio_msnm=modelo.altitud_promedio_msnm,
            altitud_minima_msnm=modelo.altitud_minima_msnm,
            altitud_maxima_msnm=modelo.altitud_maxima_msnm,
            orientacion=modelo.orientacion,
            drenaje=modelo.drenaje,
            acceso_riego=modelo.acceso_riego,
            tipo_riego=modelo.tipo_riego,
            observaciones=modelo.observaciones,
            activo=modelo.activo,
            created_at=modelo.created_at,
            updated_at=modelo.updated_at
        )