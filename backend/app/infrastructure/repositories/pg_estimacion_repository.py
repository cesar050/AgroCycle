from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.domain.entities.estimacion import Estimacion
from app.domain.repositories.i_estimacion_repository import IEstimacionRepository
from app.infrastructure.models.estimacion_model import EstimacionModel
import uuid


class PgEstimacionRepository(IEstimacionRepository):

    def __init__(self, db: Session):
        self.db = db

    def guardar(self, estimacion: Estimacion) -> Estimacion:
        modelo = EstimacionModel(
            id=uuid.UUID(estimacion.id),
            temporada_parcela_id=uuid.UUID(estimacion.temporada_parcela_id),
            version_modelo_id=estimacion.version_modelo_id,
            valor_qq_ha=estimacion.valor_qq_ha,
            valor_total_qq=estimacion.valor_total_qq,
            margen_error_porcentaje=estimacion.margen_error_porcentaje,
            valor_minimo_qq_ha=estimacion.valor_minimo_qq_ha,
            valor_maximo_qq_ha=estimacion.valor_maximo_qq_ha,
            etapa_fenologica_momento=estimacion.etapa_fenologica_momento,
            dias_desde_siembra_momento=estimacion.dias_desde_siembra_momento,
            algoritmo_usado=estimacion.algoritmo_usado,
            variables_entrada=estimacion.variables_entrada,
            factores_positivos=estimacion.factores_positivos,
            factores_negativos=estimacion.factores_negativos,
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)

    def obtener_ultima_por_temporada_parcela(
        self, temporada_parcela_id: str
    ) -> Optional[Estimacion]:
        modelo = (
            self.db.query(EstimacionModel)
            .filter(
                EstimacionModel.temporada_parcela_id == uuid.UUID(temporada_parcela_id)
            )
            .order_by(EstimacionModel.fecha_generacion.desc())
            .first()
        )
        return self._modelo_a_entidad(modelo) if modelo else None

    def listar_por_temporada_parcela(
        self, temporada_parcela_id: str
    ) -> List[Estimacion]:
        modelos = (
            self.db.query(EstimacionModel)
            .filter(
                EstimacionModel.temporada_parcela_id == uuid.UUID(temporada_parcela_id)
            )
            .order_by(EstimacionModel.fecha_generacion.asc())
            .all()
        )
        return [self._modelo_a_entidad(m) for m in modelos]

    def listar_por_temporada(self, temporada_id: str) -> List[Estimacion]:
        """
        Última estimación de cada parcela usando DISTINCT ON de PostgreSQL.
        Más eficiente que GROUP BY para este caso.
        """
        sql = text("""
            SELECT DISTINCT ON (ep.temporada_parcela_id)
                ep.id, ep.temporada_parcela_id, ep.version_modelo_id,
                ep.fecha_generacion, ep.valor_qq_ha, ep.valor_total_qq,
                ep.margen_error_porcentaje, ep.valor_minimo_qq_ha,
                ep.valor_maximo_qq_ha, ep.etapa_fenologica_momento,
                ep.dias_desde_siembra_momento, ep.algoritmo_usado,
                ep.variables_entrada, ep.factores_positivos,
                ep.factores_negativos, ep.created_at
            FROM estimaciones_produccion ep
            JOIN temporada_parcelas tp
                ON ep.temporada_parcela_id = tp.id
            WHERE tp.temporada_id = CAST(:temporada_id AS uuid)
            ORDER BY ep.temporada_parcela_id, ep.fecha_generacion DESC
        """)
        rows = self.db.execute(
            sql, {'temporada_id': temporada_id}
        ).fetchall()
        return [self._row_a_entidad(r) for r in rows]

    def _modelo_a_entidad(self, m: EstimacionModel) -> Estimacion:
        e = Estimacion(
            id=str(m.id),
            temporada_parcela_id=str(m.temporada_parcela_id),
            version_modelo_id=m.version_modelo_id,
            valor_qq_ha=float(m.valor_qq_ha),
            valor_total_qq=float(m.valor_total_qq) if m.valor_total_qq else None,
            margen_error_porcentaje=float(m.margen_error_porcentaje) if m.margen_error_porcentaje else None,
            valor_minimo_qq_ha=float(m.valor_minimo_qq_ha) if m.valor_minimo_qq_ha else None,
            valor_maximo_qq_ha=float(m.valor_maximo_qq_ha) if m.valor_maximo_qq_ha else None,
            etapa_fenologica_momento=m.etapa_fenologica_momento,
            dias_desde_siembra_momento=m.dias_desde_siembra_momento,
            algoritmo_usado=m.algoritmo_usado,
            variables_entrada=m.variables_entrada,
            factores_positivos=m.factores_positivos,
            factores_negativos=m.factores_negativos,
            fecha_generacion=m.fecha_generacion,
            created_at=m.created_at,
        )
        return e

    def _row_a_entidad(self, r) -> Estimacion:
        e = Estimacion(
            id=str(r.id),
            temporada_parcela_id=str(r.temporada_parcela_id),
            version_modelo_id=r.version_modelo_id,
            valor_qq_ha=float(r.valor_qq_ha),
            valor_total_qq=float(r.valor_total_qq) if r.valor_total_qq else None,
            margen_error_porcentaje=float(r.margen_error_porcentaje) if r.margen_error_porcentaje else None,
            valor_minimo_qq_ha=float(r.valor_minimo_qq_ha) if r.valor_minimo_qq_ha else None,
            valor_maximo_qq_ha=float(r.valor_maximo_qq_ha) if r.valor_maximo_qq_ha else None,
            etapa_fenologica_momento=r.etapa_fenologica_momento,
            dias_desde_siembra_momento=r.dias_desde_siembra_momento,
            algoritmo_usado=r.algoritmo_usado,
            variables_entrada=r.variables_entrada,
            factores_positivos=r.factores_positivos,
            factores_negativos=r.factores_negativos,
            fecha_generacion=r.fecha_generacion,
            created_at=r.created_at,
        )
        return e