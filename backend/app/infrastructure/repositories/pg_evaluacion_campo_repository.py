from typing import Optional, List
from sqlalchemy.orm import Session
from app.domain.entities.evaluacion_campo import EvaluacionCampo
from app.domain.repositories.i_evaluacion_campo_repository import IEvaluacionCampoRepository
from app.infrastructure.models.evaluacion_campo_model import EvaluacionCampoModel
import uuid


class PgEvaluacionCampoRepository(IEvaluacionCampoRepository):

    def __init__(self, db: Session):
        self.db = db

    def guardar(self, evaluacion: EvaluacionCampo) -> EvaluacionCampo:
        """Persiste una nueva evaluación de campo."""
        modelo = EvaluacionCampoModel(
            id=uuid.UUID(evaluacion.id),
            agronomo_id=uuid.UUID(evaluacion.agronomo_id),
            temporada_id=uuid.UUID(evaluacion.temporada_id),
            temporada_parcela_id=uuid.UUID(evaluacion.temporada_parcela_id) if evaluacion.temporada_parcela_id else None,
            fecha=evaluacion.fecha,
            densidad_plantas_ha=evaluacion.densidad_plantas_ha,
            incidencia_plagas_porcentaje=evaluacion.incidencia_plagas_porcentaje,
            incidencia_enfermedades_porcentaje=evaluacion.incidencia_enfermedades_porcentaje,
            estado_nutricional=evaluacion.estado_nutricional,
            estado_fenologico_confirmado=evaluacion.estado_fenologico_confirmado,
            observaciones=evaluacion.observaciones,
            alerta_generada=evaluacion.alerta_generada,
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)

    def obtener_por_id(
        self, evaluacion_id: str
    ) -> Optional[EvaluacionCampo]:
        """Busca una evaluación por su UUID."""
        modelo = self.db.query(EvaluacionCampoModel).filter(
            EvaluacionCampoModel.id == uuid.UUID(evaluacion_id)
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    def listar_por_temporada(
        self, temporada_id: str
    ) -> List[EvaluacionCampo]:
        """
        Retorna evaluaciones ordenadas cronológicamente.
        Orden ascendente para ver la evolución del cultivo
        desde el inicio hasta el final de la temporada.
        """
        modelos = self.db.query(EvaluacionCampoModel).filter(
            EvaluacionCampoModel.temporada_id == uuid.UUID(temporada_id)
        ).order_by(EvaluacionCampoModel.fecha.asc()).all()
        return [self._modelo_a_entidad(m) for m in modelos]

    def listar_por_temporada_parcela(
        self, temporada_parcela_id: str
    ) -> List[EvaluacionCampo]:
        """Retorna evaluaciones de una parcela específica."""
        modelos = self.db.query(EvaluacionCampoModel).filter(
            EvaluacionCampoModel.temporada_parcela_id == uuid.UUID(temporada_parcela_id)
        ).order_by(EvaluacionCampoModel.fecha.asc()).all()
        return [self._modelo_a_entidad(m) for m in modelos]

    def _modelo_a_entidad(
        self, m: EvaluacionCampoModel
    ) -> EvaluacionCampo:
        """Convierte modelo ORM a entidad de dominio."""
        return EvaluacionCampo(
            id=str(m.id),
            agronomo_id=str(m.agronomo_id),
            temporada_id=str(m.temporada_id),
            temporada_parcela_id=str(m.temporada_parcela_id) if m.temporada_parcela_id else None,
            fecha=m.fecha,
            densidad_plantas_ha=m.densidad_plantas_ha,
            incidencia_plagas_porcentaje=float(m.incidencia_plagas_porcentaje) if m.incidencia_plagas_porcentaje else None,
            incidencia_enfermedades_porcentaje=float(m.incidencia_enfermedades_porcentaje) if m.incidencia_enfermedades_porcentaje else None,
            estado_nutricional=m.estado_nutricional,
            estado_fenologico_confirmado=m.estado_fenologico_confirmado,
            observaciones=m.observaciones,
            alerta_generada=m.alerta_generada,
            created_at=m.created_at,
        )