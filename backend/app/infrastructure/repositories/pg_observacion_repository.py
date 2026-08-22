from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.domain.entities.observacion_tecnica import ObservacionTecnica
from app.domain.repositories.i_observacion_repository import IObservacionRepository
from app.infrastructure.models.observacion_tecnica_model import ObservacionTecnicaModel
import uuid


class PgObservacionRepository(IObservacionRepository):

    def __init__(self, db: Session):
        self.db = db

    def guardar(self, observacion: ObservacionTecnica) -> ObservacionTecnica:
        """Persiste una nueva observación técnica en la base de datos."""
        modelo = ObservacionTecnicaModel(
            id=uuid.UUID(observacion.id),
            agronomo_id=uuid.UUID(observacion.agronomo_id),
            temporada_id=uuid.UUID(observacion.temporada_id),
            temporada_parcela_id=uuid.UUID(observacion.temporada_parcela_id) if observacion.temporada_parcela_id else None,
            tipo=observacion.tipo,
            descripcion=observacion.descripcion,
            fecha=observacion.fecha,
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)

    def obtener_por_id(
        self, observacion_id: str
    ) -> Optional[ObservacionTecnica]:
        """Busca una observación por su UUID."""
        modelo = self.db.query(ObservacionTecnicaModel).filter(
            ObservacionTecnicaModel.id == uuid.UUID(observacion_id)
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    def listar_por_temporada(
        self, temporada_id: str
    ) -> List[ObservacionTecnica]:
        """
        Retorna todas las observaciones de una temporada
        ordenadas de más reciente a más antigua.
        """
        modelos = self.db.query(ObservacionTecnicaModel).filter(
            ObservacionTecnicaModel.temporada_id == uuid.UUID(temporada_id)
        ).order_by(ObservacionTecnicaModel.fecha.desc()).all()
        return [self._modelo_a_entidad(m) for m in modelos]

    def listar_por_temporada_parcela(
        self, temporada_parcela_id: str
    ) -> List[ObservacionTecnica]:
        """Retorna observaciones específicas de una parcela."""
        modelos = self.db.query(ObservacionTecnicaModel).filter(
            ObservacionTecnicaModel.temporada_parcela_id == uuid.UUID(temporada_parcela_id)
        ).order_by(ObservacionTecnicaModel.fecha.desc()).all()
        return [self._modelo_a_entidad(m) for m in modelos]

    def eliminar(self, observacion_id: str) -> bool:
        """Elimina una observación. Retorna True si se eliminó."""
        modelo = self.db.query(ObservacionTecnicaModel).filter(
            ObservacionTecnicaModel.id == uuid.UUID(observacion_id)
        ).first()
        if not modelo:
            return False
        self.db.delete(modelo)
        self.db.commit()
        return True

    def _modelo_a_entidad(
        self, m: ObservacionTecnicaModel
    ) -> ObservacionTecnica:
        """
        Convierte modelo ORM a entidad de dominio.
        Aísla la infraestructura del dominio — si cambia
        el modelo solo cambia este método.
        """
        return ObservacionTecnica(
            id=str(m.id),
            agronomo_id=str(m.agronomo_id),
            temporada_id=str(m.temporada_id),
            temporada_parcela_id=str(m.temporada_parcela_id) if m.temporada_parcela_id else None,
            tipo=m.tipo,
            descripcion=m.descripcion,
            fecha=m.fecha,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )