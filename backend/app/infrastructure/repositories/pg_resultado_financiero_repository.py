from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.domain.entities.resultado_financiero import ResultadoFinanciero
from app.domain.repositories.i_resultado_financiero_repository import IResultadoFinancieroRepository
from app.infrastructure.models.resultado_financiero_model import ResultadoFinancieroModel
import uuid


class PgResultadoFinancieroRepository(IResultadoFinancieroRepository):

    def __init__(self, db: Session):
        self.db = db

    def guardar(self, resultado: ResultadoFinanciero) -> ResultadoFinanciero:
        """
        Crea o actualiza el resultado financiero de una temporada.
        Usa upsert porque una temporada solo tiene un resultado —
        recalcular no debe crear duplicados.
        """
        modelo_existente = self.db.query(ResultadoFinancieroModel).filter(
            ResultadoFinancieroModel.temporada_id == uuid.UUID(resultado.temporada_id)
        ).first()

        if modelo_existente:
            # Actualizar el existente
            modelo_existente.ingresos_totales = resultado.ingresos_totales
            modelo_existente.costos_totales = resultado.costos_totales
            modelo_existente.costo_semillas = resultado.costo_semillas
            modelo_existente.costo_fertilizantes = resultado.costo_fertilizantes
            modelo_existente.costo_agroquimicos = resultado.costo_agroquimicos
            modelo_existente.costo_mano_obra = resultado.costo_mano_obra
            modelo_existente.costo_otros = resultado.costo_otros
            modelo_existente.ganancia_neta = resultado.ganancia_neta
            modelo_existente.margen_rentabilidad_porcentaje = resultado.margen_rentabilidad_porcentaje
            modelo_existente.costo_por_quintal = resultado.costo_por_quintal
            modelo_existente.precio_venta_promedio_qq = resultado.precio_venta_promedio_qq
            modelo_existente.produccion_total_qq = resultado.produccion_total_qq
            modelo_existente.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(modelo_existente)
            return self._modelo_a_entidad(modelo_existente)

        # Crear nuevo
        modelo = ResultadoFinancieroModel(
            id=uuid.UUID(resultado.id),
            temporada_id=uuid.UUID(resultado.temporada_id),
            ingresos_totales=resultado.ingresos_totales,
            costos_totales=resultado.costos_totales,
            costo_semillas=resultado.costo_semillas,
            costo_fertilizantes=resultado.costo_fertilizantes,
            costo_agroquimicos=resultado.costo_agroquimicos,
            costo_mano_obra=resultado.costo_mano_obra,
            costo_otros=resultado.costo_otros,
            ganancia_neta=resultado.ganancia_neta,
            margen_rentabilidad_porcentaje=resultado.margen_rentabilidad_porcentaje,
            costo_por_quintal=resultado.costo_por_quintal,
            precio_venta_promedio_qq=resultado.precio_venta_promedio_qq,
            produccion_total_qq=resultado.produccion_total_qq,
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)

    def obtener_por_temporada(
        self, temporada_id: str
    ) -> Optional[ResultadoFinanciero]:
        """Retorna el resultado financiero de una temporada si existe."""
        modelo = self.db.query(ResultadoFinancieroModel).filter(
            ResultadoFinancieroModel.temporada_id == uuid.UUID(temporada_id)
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    def listar_por_agricultor(
        self, agricultor_id: str
    ) -> List[ResultadoFinanciero]:
        """
        Retorna resultados financieros de todas las temporadas
        del agricultor para el comparativo entre temporadas.
        Hace el JOIN en BD — más eficiente que múltiples queries.
        """
        sql = text("""
            SELECT rf.*
            FROM resultados_financieros rf
            JOIN temporadas t ON rf.temporada_id = t.id
            JOIN agricultores a ON t.agricultor_id = a.id
            WHERE a.usuario_id = CAST(:agricultor_id AS uuid)
            ORDER BY t.fecha_inicio DESC
        """)
        rows = self.db.execute(
            sql, {'agricultor_id': agricultor_id}
        ).fetchall()
        return [self._row_a_entidad(r) for r in rows]

    def _modelo_a_entidad(self, m: ResultadoFinancieroModel) -> ResultadoFinanciero:
        """Convierte modelo ORM a entidad de dominio."""
        r = ResultadoFinanciero(
            id=str(m.id),
            temporada_id=str(m.temporada_id),
            ingresos_totales=float(m.ingresos_totales or 0),
            costos_totales=float(m.costos_totales or 0),
            costo_semillas=float(m.costo_semillas or 0),
            costo_fertilizantes=float(m.costo_fertilizantes or 0),
            costo_agroquimicos=float(m.costo_agroquimicos or 0),
            costo_mano_obra=float(m.costo_mano_obra or 0),
            costo_otros=float(m.costo_otros or 0),
            ganancia_neta=float(m.ganancia_neta) if m.ganancia_neta is not None else None,
            margen_rentabilidad_porcentaje=float(m.margen_rentabilidad_porcentaje) if m.margen_rentabilidad_porcentaje is not None else None,
            costo_por_quintal=float(m.costo_por_quintal) if m.costo_por_quintal is not None else None,
            precio_venta_promedio_qq=float(m.precio_venta_promedio_qq) if m.precio_venta_promedio_qq is not None else None,
            produccion_total_qq=float(m.produccion_total_qq) if m.produccion_total_qq is not None else None,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        return r

    def _row_a_entidad(self, r) -> ResultadoFinanciero:
        """Convierte fila de query raw a entidad de dominio."""
        return ResultadoFinanciero(
            id=str(r.id),
            temporada_id=str(r.temporada_id),
            ingresos_totales=float(r.ingresos_totales or 0),
            costos_totales=float(r.costos_totales or 0),
            costo_semillas=float(r.costo_semillas or 0),
            costo_fertilizantes=float(r.costo_fertilizantes or 0),
            costo_agroquimicos=float(r.costo_agroquimicos or 0),
            costo_mano_obra=float(r.costo_mano_obra or 0),
            costo_otros=float(r.costo_otros or 0),
            ganancia_neta=float(r.ganancia_neta) if r.ganancia_neta is not None else None,
            margen_rentabilidad_porcentaje=float(r.margen_rentabilidad_porcentaje) if r.margen_rentabilidad_porcentaje is not None else None,
            costo_por_quintal=float(r.costo_por_quintal) if r.costo_por_quintal is not None else None,
            precio_venta_promedio_qq=float(r.precio_venta_promedio_qq) if r.precio_venta_promedio_qq is not None else None,
            produccion_total_qq=float(r.produccion_total_qq) if r.produccion_total_qq is not None else None,
        )