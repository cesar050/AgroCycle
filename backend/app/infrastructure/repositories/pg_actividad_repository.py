"""
Implementacion PostgreSQL del repositorio de Actividad.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.domain.entities.actividad import Actividad
from app.domain.repositories.i_actividad_repository import IActividadRepository
from app.infrastructure.models.actividad_model import ActividadModel
import uuid


class PgActividadRepository(IActividadRepository):

    def __init__(self, db: Session):
        self.db = db

    def guardar(self, actividad: Actividad) -> Actividad:
        modelo = ActividadModel(
            id=uuid.UUID(actividad.id),
            temporada_id=uuid.UUID(actividad.temporada_id),
            temporada_parcela_id=uuid.UUID(actividad.temporada_parcela_id) if actividad.temporada_parcela_id else None,
            tipo_actividad_id=actividad.tipo_actividad_id,
            fecha=actividad.fecha,
            descripcion=actividad.descripcion,
            observaciones=actividad.observaciones,
            costo_total=actividad.costo_total,
            registrado_por=uuid.UUID(actividad.registrado_por) if actividad.registrado_por else None
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)

    def buscar_por_id(self, actividad_id: str) -> Optional[Actividad]:
        modelo = self.db.query(ActividadModel).filter(
            ActividadModel.id == uuid.UUID(actividad_id)
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    def listar_por_temporada(self, temporada_id: str) -> List[Actividad]:
        modelos = self.db.query(ActividadModel).filter(
            ActividadModel.temporada_id == uuid.UUID(temporada_id)
        ).order_by(ActividadModel.fecha.desc()).all()
        return [self._modelo_a_entidad(m) for m in modelos]

    def listar_por_temporada_parcela(
        self, temporada_parcela_id: str
    ) -> List[Actividad]:
        modelos = self.db.query(ActividadModel).filter(
            ActividadModel.temporada_parcela_id == uuid.UUID(temporada_parcela_id)
        ).order_by(ActividadModel.fecha.desc()).all()
        return [self._modelo_a_entidad(m) for m in modelos]

    def _modelo_a_entidad(self, modelo: ActividadModel) -> Actividad:
        return Actividad(
            id=str(modelo.id),
            temporada_id=str(modelo.temporada_id),
            temporada_parcela_id=str(modelo.temporada_parcela_id) if modelo.temporada_parcela_id else None,
            tipo_actividad_id=modelo.tipo_actividad_id,
            fecha=modelo.fecha,
            descripcion=modelo.descripcion,
            observaciones=modelo.observaciones,
            costo_total=float(modelo.costo_total or 0),
            registrado_por=str(modelo.registrado_por) if modelo.registrado_por else None,
            created_at=modelo.created_at,
            updated_at=modelo.updated_at
        )