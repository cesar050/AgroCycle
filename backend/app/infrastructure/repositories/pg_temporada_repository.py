"""
Implementacion PostgreSQL del repositorio de Temporada.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.domain.entities.temporada import Temporada
from app.domain.repositories.i_temporada_repository import ITemporadaRepository
from app.infrastructure.models.temporada_model import TemporadaModel
import uuid


class PgTemporadaRepository(ITemporadaRepository):

    def __init__(self, db: Session):
        self.db = db

    def guardar(self, temporada: Temporada) -> Temporada:
        modelo = TemporadaModel(
            id=uuid.UUID(temporada.id),
            agricultor_id=uuid.UUID(temporada.agricultor_id),
            finca_id=uuid.UUID(temporada.finca_id),
            cultivo_id=temporada.cultivo_id,
            nombre=temporada.nombre,
            fecha_inicio=temporada.fecha_inicio,
            fecha_fin_estimada=temporada.fecha_fin_estimada,
            fecha_fin_real=temporada.fecha_fin_real,
            estado=temporada.estado,
            observaciones=temporada.observaciones
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)

    def buscar_por_id(self, temporada_id: str) -> Optional[Temporada]:
        modelo = self.db.query(TemporadaModel).filter(
            TemporadaModel.id == uuid.UUID(temporada_id)
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    def listar_por_agricultor(self, agricultor_id: str) -> List[Temporada]:
        modelos = self.db.query(TemporadaModel).filter(
            TemporadaModel.agricultor_id == uuid.UUID(agricultor_id)
        ).order_by(TemporadaModel.created_at.desc()).all()
        return [self._modelo_a_entidad(m) for m in modelos]

    def listar_activas_por_agricultor(self, agricultor_id: str) -> List[Temporada]:
        modelos = self.db.query(TemporadaModel).filter(
            TemporadaModel.agricultor_id == uuid.UUID(agricultor_id),
            TemporadaModel.estado == 'activa'
        ).order_by(TemporadaModel.created_at.desc()).all()
        return [self._modelo_a_entidad(m) for m in modelos]

    def actualizar(self, temporada: Temporada) -> Temporada:
        modelo = self.db.query(TemporadaModel).filter(
            TemporadaModel.id == uuid.UUID(temporada.id)
        ).first()
        if not modelo:
            raise ValueError(f"Temporada {temporada.id} no encontrada")
        modelo.nombre = temporada.nombre
        modelo.fecha_fin_estimada = temporada.fecha_fin_estimada
        modelo.fecha_fin_real = temporada.fecha_fin_real
        modelo.estado = temporada.estado
        modelo.observaciones = temporada.observaciones
        modelo.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)

    def _modelo_a_entidad(self, modelo: TemporadaModel) -> Temporada:
        return Temporada(
            id=str(modelo.id),
            agricultor_id=str(modelo.agricultor_id),
            finca_id=str(modelo.finca_id),
            cultivo_id=modelo.cultivo_id,
            nombre=modelo.nombre,
            fecha_inicio=modelo.fecha_inicio,
            fecha_fin_estimada=modelo.fecha_fin_estimada,
            fecha_fin_real=modelo.fecha_fin_real,
            estado=modelo.estado,
            observaciones=modelo.observaciones,
            created_at=modelo.created_at,
            updated_at=modelo.updated_at
        )