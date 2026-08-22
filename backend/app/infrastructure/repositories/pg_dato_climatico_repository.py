"""
Implementacion PostgreSQL del repositorio de DatoClimatico.
"""
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.domain.entities.dato_climatico import DatoClimatico
from app.domain.repositories.i_dato_climatico_repository import IDatoClimaticoRepository
from app.infrastructure.models.dato_climatico_model import DatoClimaticoModel
import uuid


class PgDatoClimaticoRepository(IDatoClimaticoRepository):

    def __init__(self, db: Session):
        self.db = db

    def guardar(self, dato: DatoClimatico) -> DatoClimatico:
        modelo = DatoClimaticoModel(
            parcela_id=uuid.UUID(dato.parcela_id),
            temporada_id=uuid.UUID(dato.temporada_id) if dato.temporada_id else None,
            fecha=dato.fecha,
            precipitacion_mm=dato.precipitacion_mm,
            temperatura_max_c=dato.temperatura_max_c,
            temperatura_min_c=dato.temperatura_min_c,
            temperatura_promedio_c=dato.temperatura_promedio_c,
            humedad_relativa_porcentaje=dato.humedad_relativa_porcentaje,
            radiacion_solar_mj_m2=dato.radiacion_solar_mj_m2,
            velocidad_viento_km_h=dato.velocidad_viento_km_h,
            evapotranspiracion_mm=dato.evapotranspiracion_mm,
            fuente=dato.fuente
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)

    def guardar_lote(self, datos: List[DatoClimatico]) -> int:
        """Guarda multiples datos climaticos en una sola transaccion."""
        guardados = 0
        for dato in datos:
            modelo = DatoClimaticoModel(
                parcela_id=uuid.UUID(dato.parcela_id),
                temporada_id=uuid.UUID(dato.temporada_id) if dato.temporada_id else None,
                fecha=dato.fecha,
                precipitacion_mm=dato.precipitacion_mm,
                temperatura_max_c=dato.temperatura_max_c,
                temperatura_min_c=dato.temperatura_min_c,
                temperatura_promedio_c=dato.temperatura_promedio_c,
                humedad_relativa_porcentaje=dato.humedad_relativa_porcentaje,
                radiacion_solar_mj_m2=dato.radiacion_solar_mj_m2,
                velocidad_viento_km_h=dato.velocidad_viento_km_h,
                evapotranspiracion_mm=dato.evapotranspiracion_mm,
                fuente=dato.fuente
            )
            self.db.add(modelo)
            guardados += 1
        self.db.commit()
        return guardados

    def buscar_por_parcela_y_fecha(
        self, parcela_id: str, fecha: date
    ) -> Optional[DatoClimatico]:
        modelo = self.db.query(DatoClimaticoModel).filter(
            DatoClimaticoModel.parcela_id == uuid.UUID(parcela_id),
            DatoClimaticoModel.fecha == fecha
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    def listar_por_parcela_y_rango(
        self, parcela_id: str, fecha_inicio: date, fecha_fin: date
    ) -> List[DatoClimatico]:
        modelos = self.db.query(DatoClimaticoModel).filter(
            DatoClimaticoModel.parcela_id == uuid.UUID(parcela_id),
            DatoClimaticoModel.fecha >= fecha_inicio,
            DatoClimaticoModel.fecha <= fecha_fin
        ).order_by(DatoClimaticoModel.fecha.asc()).all()
        return [self._modelo_a_entidad(m) for m in modelos]

    def actualizar_precipitacion(
        self, parcela_id: str, fecha: date, precipitacion_adicional: float
    ) -> bool:
        """Suma precipitacion adicional por riego al dato existente."""
        resultado = self.db.execute(
            text("""
                UPDATE datos_climaticos
                SET precipitacion_mm = precipitacion_mm + :adicional,
                    fuente = 'manual'
                WHERE parcela_id = CAST(:parcela_id AS uuid)
                AND fecha = :fecha
            """),
            {
                "adicional": precipitacion_adicional,
                "parcela_id": parcela_id,
                "fecha": fecha
            }
        )
        self.db.commit()
        return resultado.rowcount > 0

    def fechas_existentes(
        self, parcela_id: str, fecha_inicio: date, fecha_fin: date
    ) -> set:
        """Retorna el conjunto de fechas que ya tienen datos guardados."""
        resultado = self.db.execute(
            text("""
                SELECT fecha FROM datos_climaticos
                WHERE parcela_id = CAST(:parcela_id AS uuid)
                AND fecha BETWEEN :fecha_inicio AND :fecha_fin
            """),
            {
                "parcela_id": parcela_id,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin
            }
        ).fetchall()
        return {str(r.fecha) for r in resultado}

    def _modelo_a_entidad(self, modelo: DatoClimaticoModel) -> DatoClimatico:
        return DatoClimatico(
            parcela_id=str(modelo.parcela_id),
            fecha=modelo.fecha,
            precipitacion_mm=float(modelo.precipitacion_mm or 0),
            temperatura_max_c=float(modelo.temperatura_max_c) if modelo.temperatura_max_c else None,
            temperatura_min_c=float(modelo.temperatura_min_c) if modelo.temperatura_min_c else None,
            temperatura_promedio_c=float(modelo.temperatura_promedio_c) if modelo.temperatura_promedio_c else None,
            humedad_relativa_porcentaje=float(modelo.humedad_relativa_porcentaje) if modelo.humedad_relativa_porcentaje else None,
            radiacion_solar_mj_m2=float(modelo.radiacion_solar_mj_m2) if modelo.radiacion_solar_mj_m2 else None,
            velocidad_viento_km_h=float(modelo.velocidad_viento_km_h) if modelo.velocidad_viento_km_h else None,
            evapotranspiracion_mm=float(modelo.evapotranspiracion_mm) if modelo.evapotranspiracion_mm else None,
            temporada_id=str(modelo.temporada_id) if modelo.temporada_id else None,
            fuente=modelo.fuente,
            created_at=modelo.created_at
        )