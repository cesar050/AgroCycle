"""
Servicio de consulta de datos climaticos via Open-Meteo API.
Open-Meteo es gratuito, no requiere API key y tiene datos
historicos desde 1940 y pronosticos hasta 7 dias.
Se usa para obtener precipitacion, temperatura y ET0
para las coordenadas exactas de cada parcela.
"""
import requests
import os
from datetime import date, timedelta
from app.infrastructure.logging.logger import configurar_logger

logger = configurar_logger('openmeteo_service')

OPENMETEO_FORECAST_URL = os.getenv(
    'OPENMETEO_BASE_URL',
    'https://api.open-meteo.com/v1'
)
OPENMETEO_ARCHIVE_URL = os.getenv(
    'OPENMETEO_ARCHIVE_URL',
    'https://archive-api.open-meteo.com/v1'
)


def obtener_clima_historico(
    latitud: float,
    longitud: float,
    fecha_inicio: date,
    fecha_fin: date
) -> list:
    """
    Obtiene datos climaticos historicos para un rango de fechas.
    Usa la Archive API de Open-Meteo que tiene datos desde 1940.
    Retorna una lista de diccionarios con datos por dia.

    Args:
        latitud: Latitud de la parcela
        longitud: Longitud de la parcela
        fecha_inicio: Fecha de inicio del periodo
        fecha_fin: Fecha de fin del periodo

    Returns:
        Lista de diccionarios con datos climaticos por dia
    """
    try:
        url = f"{OPENMETEO_ARCHIVE_URL}/archive"
        params = {
            "latitude": latitud,
            "longitude": longitud,
            "start_date": fecha_inicio.isoformat(),
            "end_date": fecha_fin.isoformat(),
            "daily": [
                "precipitation_sum",
                "temperature_2m_max",
                "temperature_2m_min",
                "temperature_2m_mean",
                "relative_humidity_2m_mean",
                "shortwave_radiation_sum",
                "wind_speed_10m_max",
                "et0_fao_evapotranspiration"
            ],
            "timezone": "America/Guayaquil"
        }

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if 'daily' not in data:
            logger.warning(f"Open-Meteo no retorno datos diarios para ({latitud}, {longitud})")
            return []

        daily = data['daily']
        fechas = daily.get('time', [])
        precipitacion = daily.get('precipitation_sum', [])
        temp_max = daily.get('temperature_2m_max', [])
        temp_min = daily.get('temperature_2m_min', [])
        temp_media = daily.get('temperature_2m_mean', [])
        humedad = daily.get('relative_humidity_2m_mean', [])
        radiacion = daily.get('shortwave_radiation_sum', [])
        viento = daily.get('wind_speed_10m_max', [])
        et0 = daily.get('et0_fao_evapotranspiration', [])

        resultados = []
        for i, fecha in enumerate(fechas):
            resultados.append({
                "fecha": fecha,
                "precipitacion_mm": precipitacion[i] if i < len(precipitacion) else None,
                "temperatura_max_c": temp_max[i] if i < len(temp_max) else None,
                "temperatura_min_c": temp_min[i] if i < len(temp_min) else None,
                "temperatura_promedio_c": temp_media[i] if i < len(temp_media) else None,
                "humedad_relativa_porcentaje": humedad[i] if i < len(humedad) else None,
                "radiacion_solar_mj_m2": radiacion[i] if i < len(radiacion) else None,
                "velocidad_viento_km_h": viento[i] if i < len(viento) else None,
                "evapotranspiracion_mm": et0[i] if i < len(et0) else None,
                "fuente": "api"
            })

        logger.info(
            f"Clima historico obtenido: {len(resultados)} dias "
            f"para ({latitud}, {longitud}) "
            f"del {fecha_inicio} al {fecha_fin}"
        )
        return resultados

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout consultando Open-Meteo para ({latitud}, {longitud})")
    except requests.exceptions.ConnectionError:
        logger.warning(f"Sin conexion a Open-Meteo para ({latitud}, {longitud})")
    except Exception as e:
        logger.error(f"Error consultando Open-Meteo: {str(e)}")

    return []


def obtener_clima_forecast(
    latitud: float,
    longitud: float,
    dias: int = 7
) -> list:
    """
    Obtiene el pronostico climatico para los proximos dias.
    Usa la Forecast API de Open-Meteo.
    Util para alertas preventivas de sequia o exceso de lluvia.

    Args:
        latitud: Latitud de la parcela
        longitud: Longitud de la parcela
        dias: Numero de dias de pronostico (max 16)

    Returns:
        Lista de diccionarios con pronostico por dia
    """
    try:
        url = f"{OPENMETEO_FORECAST_URL}/forecast"
        params = {
            "latitude": latitud,
            "longitude": longitud,
            "forecast_days": min(dias, 16),
            "daily": [
                "precipitation_sum",
                "temperature_2m_max",
                "temperature_2m_min",
                "et0_fao_evapotranspiration",
                "precipitation_probability_max"
            ],
            "timezone": "America/Guayaquil"
        }

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if 'daily' not in data:
            return []

        daily = data['daily']
        fechas = daily.get('time', [])
        precipitacion = daily.get('precipitation_sum', [])
        temp_max = daily.get('temperature_2m_max', [])
        temp_min = daily.get('temperature_2m_min', [])
        et0 = daily.get('et0_fao_evapotranspiration', [])
        prob_lluvia = daily.get('precipitation_probability_max', [])

        resultados = []
        for i, fecha in enumerate(fechas):
            resultados.append({
                "fecha": fecha,
                "precipitacion_mm": precipitacion[i] if i < len(precipitacion) else None,
                "temperatura_max_c": temp_max[i] if i < len(temp_max) else None,
                "temperatura_min_c": temp_min[i] if i < len(temp_min) else None,
                "evapotranspiracion_mm": et0[i] if i < len(et0) else None,
                "probabilidad_lluvia_porcentaje": prob_lluvia[i] if i < len(prob_lluvia) else None
            })

        logger.info(f"Forecast obtenido: {len(resultados)} dias para ({latitud}, {longitud})")
        return resultados

    except Exception as e:
        logger.error(f"Error obteniendo forecast: {str(e)}")

    return []


def obtener_clima_hoy(latitud: float, longitud: float) -> dict:
    """
    Obtiene los datos climaticos de hoy.
    Combina datos historicos de ayer con forecast de hoy.
    """
    hoy = date.today()
    ayer = hoy - timedelta(days=1)

    datos = obtener_clima_historico(latitud, longitud, ayer, hoy)
    if datos:
        return datos[-1]
    return {}