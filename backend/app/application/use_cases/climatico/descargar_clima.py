"""
Caso de uso: Descargar datos climaticos de Open-Meteo.
Ahora usa el repositorio IDatoClimaticoRepository
siguiendo Clean Architecture.
"""
from datetime import date
from app.domain.entities.dato_climatico import DatoClimatico
from app.domain.repositories.i_dato_climatico_repository import IDatoClimaticoRepository
from app.infrastructure.external.openmeteo.openmeteo_service import (
    obtener_clima_historico,
    obtener_clima_forecast
)
from app.infrastructure.logging.logger import configurar_logger, log_caso_de_uso

logger = configurar_logger('descargar_clima')


class DescargarClimaUseCase:

    def __init__(self, dato_climatico_repository: IDatoClimaticoRepository):
        self.repo = dato_climatico_repository

    @log_caso_de_uso('descargar_clima_historico')
    def ejecutar(
        self,
        parcela_id: str,
        latitud: float,
        longitud: float,
        fecha_inicio: date,
        fecha_fin: date,
        temporada_id: str = None
    ) -> dict:
        """
        Descarga datos climaticos historicos y los guarda via repositorio.
        """
        datos_api = obtener_clima_historico(latitud, longitud, fecha_inicio, fecha_fin)

        if not datos_api:
            return {
                "mensaje": "No se pudieron obtener datos climaticos",
                "total_descargado": 0,
                "total_guardado": 0
            }

        fechas_existentes = self.repo.fechas_existentes(
            parcela_id, fecha_inicio, fecha_fin
        )

        datos_nuevos = []
        for dato in datos_api:
            if dato['fecha'] in fechas_existentes:
                continue
            datos_nuevos.append(DatoClimatico(
                parcela_id=parcela_id,
                temporada_id=temporada_id,
                fecha=date.fromisoformat(dato['fecha']),
                precipitacion_mm=dato.get('precipitacion_mm') or 0,
                temperatura_max_c=dato.get('temperatura_max_c'),
                temperatura_min_c=dato.get('temperatura_min_c'),
                temperatura_promedio_c=dato.get('temperatura_promedio_c'),
                humedad_relativa_porcentaje=dato.get('humedad_relativa_porcentaje'),
                radiacion_solar_mj_m2=dato.get('radiacion_solar_mj_m2'),
                velocidad_viento_km_h=dato.get('velocidad_viento_km_h'),
                evapotranspiracion_mm=dato.get('evapotranspiracion_mm'),
                fuente='api'
            ))

        guardados = self.repo.guardar_lote(datos_nuevos) if datos_nuevos else 0

        logger.info(
            f"Clima guardado: {guardados} dias nuevos para parcela {parcela_id}"
        )

        return {
            "mensaje": "Datos climaticos actualizados exitosamente",
            "total_descargado": len(datos_api),
            "total_guardado": guardados,
            "total_existentes": len(fechas_existentes),
            "fecha_inicio": fecha_inicio.isoformat(),
            "fecha_fin": fecha_fin.isoformat()
        }

    def obtener_forecast(
        self,
        parcela_id: str,
        latitud: float,
        longitud: float,
        dias: int = 7
    ) -> list:
        return obtener_clima_forecast(latitud, longitud, dias)