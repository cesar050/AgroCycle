from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, case
from app.domain.entities.recomendacion_agronomica import RecomendacionAgronomica
from app.domain.repositories.i_recomendacion_repository import IRecomendacionRepository
from app.infrastructure.models.recomendacion_agronomica_model import RecomendacionAgronomicaModel
import uuid


class PgRecomendacionRepository(IRecomendacionRepository):

    def __init__(self, db: Session):
        self.db = db

    def guardar(
        self, recomendacion: RecomendacionAgronomica
    ) -> RecomendacionAgronomica:
        """Persiste una nueva recomendación agronómica."""
        modelo = RecomendacionAgronomicaModel(
            id=uuid.UUID(recomendacion.id),
            agronomo_id=uuid.UUID(recomendacion.agronomo_id),
            temporada_id=uuid.UUID(recomendacion.temporada_id),
            temporada_parcela_id=uuid.UUID(recomendacion.temporada_parcela_id) if recomendacion.temporada_parcela_id else None,
            tipo=recomendacion.tipo,
            descripcion=recomendacion.descripcion,
            urgencia=recomendacion.urgencia,
            fecha=recomendacion.fecha,
            fecha_limite=recomendacion.fecha_limite,
            leida=recomendacion.leida,
            implementada=recomendacion.implementada,
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)

    def obtener_por_id(
        self, recomendacion_id: str
    ) -> Optional[RecomendacionAgronomica]:
        """Busca una recomendación por su UUID."""
        modelo = self.db.query(RecomendacionAgronomicaModel).filter(
            RecomendacionAgronomicaModel.id == uuid.UUID(recomendacion_id)
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    def listar_por_temporada(
        self, temporada_id: str
    ) -> List[RecomendacionAgronomica]:
        """
        Retorna recomendaciones ordenadas por urgencia primero.
        Las urgentes aparecen siempre arriba para que el agricultor
        las vea inmediatamente al abrir el módulo.
        Orden: alta → media → baja, luego por fecha descendente.
        """
        orden_urgencia = case(
            (RecomendacionAgronomicaModel.urgencia == 'alta', 1),
            (RecomendacionAgronomicaModel.urgencia == 'media', 2),
            (RecomendacionAgronomicaModel.urgencia == 'baja', 3),
            else_=4
        )
        modelos = self.db.query(RecomendacionAgronomicaModel).filter(
            RecomendacionAgronomicaModel.temporada_id == uuid.UUID(temporada_id)
        ).order_by(
            orden_urgencia,
            RecomendacionAgronomicaModel.fecha.desc()
        ).all()
        return [self._modelo_a_entidad(m) for m in modelos]

    def listar_no_leidas_por_agricultor(
        self, agricultor_id: str
    ) -> List[RecomendacionAgronomica]:
        """
        Retorna recomendaciones no leídas del agricultor.
        Hace JOIN con temporadas y agricultores para filtrar
        solo las que pertenecen al agricultor autenticado.
        Sirve para el badge de notificaciones del dashboard.
        """
        rows = self.db.execute(
            text("""
                SELECT ra.*
                FROM recomendaciones_agronomicas ra
                JOIN temporadas t ON ra.temporada_id = t.id
                JOIN agricultores a ON t.agricultor_id = a.id
                WHERE a.usuario_id = CAST(:agricultor_id AS uuid)
                  AND ra.leida = false
                ORDER BY
                    CASE ra.urgencia
                        WHEN 'alta' THEN 1
                        WHEN 'media' THEN 2
                        WHEN 'baja' THEN 3
                    END,
                    ra.fecha DESC
            """),
            {'agricultor_id': agricultor_id}
        ).fetchall()
        return [self._row_a_entidad(r) for r in rows]

    def marcar_leida(self, recomendacion_id: str) -> bool:
        """Marca una recomendación como leída por el agricultor."""
        modelo = self.db.query(RecomendacionAgronomicaModel).filter(
            RecomendacionAgronomicaModel.id == uuid.UUID(recomendacion_id)
        ).first()
        if not modelo:
            return False
        modelo.leida = True
        modelo.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    def _modelo_a_entidad(
        self, m: RecomendacionAgronomicaModel
    ) -> RecomendacionAgronomica:
        """Convierte modelo ORM a entidad de dominio."""
        return RecomendacionAgronomica(
            id=str(m.id),
            agronomo_id=str(m.agronomo_id),
            temporada_id=str(m.temporada_id),
            temporada_parcela_id=str(m.temporada_parcela_id) if m.temporada_parcela_id else None,
            tipo=m.tipo,
            descripcion=m.descripcion,
            urgencia=m.urgencia,
            fecha=m.fecha,
            fecha_limite=m.fecha_limite,
            leida=m.leida,
            implementada=m.implementada,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def _row_a_entidad(self, r) -> RecomendacionAgronomica:
        """Convierte fila de query raw a entidad de dominio."""
        return RecomendacionAgronomica(
            id=str(r.id),
            agronomo_id=str(r.agronomo_id),
            temporada_id=str(r.temporada_id),
            temporada_parcela_id=str(r.temporada_parcela_id) if r.temporada_parcela_id else None,
            tipo=r.tipo,
            descripcion=r.descripcion,
            urgencia=r.urgencia,
            fecha=r.fecha,
            fecha_limite=r.fecha_limite,
            leida=r.leida,
            implementada=r.implementada,
        )