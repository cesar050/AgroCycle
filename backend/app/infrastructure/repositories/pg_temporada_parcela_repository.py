"""
Implementacion PostgreSQL del repositorio de TemporadaParcela.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.domain.entities.temporada_parcela import TemporadaParcela
from app.domain.repositories.i_temporada_parcela_repository import ITemporadaParcelaRepository
from app.infrastructure.models.temporada_parcela_model import TemporadaParcelaModel
import uuid


class PgTemporadaParcelaRepository(ITemporadaParcelaRepository):

    def __init__(self, db: Session):
        self.db = db

    def guardar(self, tp: TemporadaParcela) -> TemporadaParcela:
        modelo = TemporadaParcelaModel(
            id=uuid.UUID(tp.id),
            temporada_id=uuid.UUID(tp.temporada_id),
            parcela_id=uuid.UUID(tp.parcela_id),
            variedad_semilla_id=tp.variedad_semilla_id,
            fecha_siembra=tp.fecha_siembra,
            densidad_siembra_kg_ha=tp.densidad_siembra_kg_ha,
            cantidad_semilla_kg=tp.cantidad_semilla_kg,
            estado_fenologico=tp.estado_fenologico,
            activo=tp.activo
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)

    def buscar_por_id(self, tp_id: str) -> Optional[TemporadaParcela]:
        modelo = self.db.query(TemporadaParcelaModel).filter(
            TemporadaParcelaModel.id == uuid.UUID(tp_id)
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    def listar_por_temporada(self, temporada_id: str) -> List[TemporadaParcela]:
        modelos = self.db.query(TemporadaParcelaModel).filter(
            TemporadaParcelaModel.temporada_id == uuid.UUID(temporada_id),
            TemporadaParcelaModel.activo == True
        ).all()
        return [self._modelo_a_entidad(m) for m in modelos]

    def actualizar(self, tp: TemporadaParcela) -> TemporadaParcela:
        modelo = self.db.query(TemporadaParcelaModel).filter(
            TemporadaParcelaModel.id == uuid.UUID(tp.id)
        ).first()
        if not modelo:
            raise ValueError(f"TemporadaParcela {tp.id} no encontrada")
        modelo.variedad_semilla_id = tp.variedad_semilla_id
        modelo.fecha_siembra = tp.fecha_siembra
        modelo.densidad_siembra_kg_ha = tp.densidad_siembra_kg_ha
        modelo.cantidad_semilla_kg = tp.cantidad_semilla_kg
        modelo.estado_fenologico = tp.estado_fenologico
        modelo.dias_desde_siembra = tp.dias_desde_siembra
        modelo.avance_ciclo_porcentaje = tp.avance_ciclo_porcentaje
        modelo.produccion_real_qq = tp.produccion_real_qq
        modelo.fecha_cosecha = tp.fecha_cosecha
        modelo.precio_venta_qq = tp.precio_venta_qq
        modelo.volumen_vendido_qq = tp.volumen_vendido_qq
        modelo.ingresos_totales = tp.ingresos_totales
        modelo.produccion_autoconsumo_qq = tp.produccion_autoconsumo_qq
        modelo.activo = tp.activo
        modelo.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)

    def existe_parcela_en_temporada(self, parcela_id: str, temporada_id: str) -> bool:
        return self.db.query(TemporadaParcelaModel).filter(
            TemporadaParcelaModel.parcela_id == uuid.UUID(parcela_id),
            TemporadaParcelaModel.temporada_id == uuid.UUID(temporada_id),
            TemporadaParcelaModel.activo == True
        ).count() > 0

    def _modelo_a_entidad(self, modelo: TemporadaParcelaModel) -> TemporadaParcela:
        return TemporadaParcela(
            id=str(modelo.id),
            temporada_id=str(modelo.temporada_id),
            parcela_id=str(modelo.parcela_id),
            variedad_semilla_id=modelo.variedad_semilla_id,
            fecha_siembra=modelo.fecha_siembra,
            densidad_siembra_kg_ha=modelo.densidad_siembra_kg_ha,
            cantidad_semilla_kg=modelo.cantidad_semilla_kg,
            estado_fenologico=modelo.estado_fenologico,
            dias_desde_siembra=modelo.dias_desde_siembra,
            avance_ciclo_porcentaje=modelo.avance_ciclo_porcentaje,
            produccion_real_qq=modelo.produccion_real_qq,
            fecha_cosecha=modelo.fecha_cosecha,
            precio_venta_qq=modelo.precio_venta_qq,
            volumen_vendido_qq=modelo.volumen_vendido_qq,
            ingresos_totales=modelo.ingresos_totales,
            produccion_autoconsumo_qq=modelo.produccion_autoconsumo_qq,
            activo=modelo.activo,
            created_at=modelo.created_at,
            updated_at=modelo.updated_at
        )