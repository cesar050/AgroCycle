"""
Servicio de consulta de datos topograficos via OpenTopoData NASA SRTM.
Genera una grilla inteligente de puntos DENTRO del poligono real
usando Shapely para distribuirlos correctamente.
La cantidad de puntos escala segun el tamano de la parcela.
"""
import requests
import os
import math
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from app.infrastructure.logging.logger import configurar_logger

logger = configurar_logger('topografia_service')

OPENTOPODATA_URL = os.getenv(
    'OPENTOPODATA_BASE_URL',
    'https://api.opentopodata.org/v1'
)


def determinar_tamano_grilla(superficie_ha: float) -> int:
    """
    Determina el tamano de la grilla segun la superficie de la parcela.
    La resolucion SRTM es 30 metros, no tiene sentido poner mas puntos
    de los que caben dentro de un pixel SRTM.

    Returns:
        Numero de divisiones por lado de la grilla cuadrada
    """
    if superficie_ha < 0.5:
        return 8    # antes 5 → ahora 8x8 = 64 puntos
    elif superficie_ha < 1.0:
        return 10   # antes 7 → ahora 10x10 = 100 puntos
    elif superficie_ha < 2.0:
        return 12
    elif superficie_ha < 5.0:
        return 14
    else:
        return 16

def generar_puntos_dentro_poligono(
    coordenadas: list,
    superficie_ha: float
) -> list:
    """
    Genera puntos distribuidos uniformemente DENTRO del poligono real.
    Usa Shapely para verificar que cada punto cae dentro del poligono
    y no en zonas externas.

    Args:
        coordenadas: Lista de pares [longitud, latitud]
        superficie_ha: Superficie de la parcela en hectareas

    Returns:
        Lista de tuplas (latitud, longitud) de puntos dentro del poligono
    """
    # Crear poligono Shapely desde las coordenadas
    # Shapely usa (longitud, latitud) igual que GeoJSON
    poligono = Polygon([(p[0], p[1]) for p in coordenadas])

    # Obtener el bounding box del poligono
    min_lng, min_lat, max_lng, max_lat = poligono.bounds

    # Determinar tamano de grilla segun superficie
    n = determinar_tamano_grilla(superficie_ha)

    # Generar grilla de candidatos
    puntos_validos = []
    for i in range(n):
        for j in range(n):
            # Interpolacion lineal para distribuir puntos uniformemente
            lng = min_lng + (max_lng - min_lng) * (i + 0.5) / n
            lat = min_lat + (max_lat - min_lat) * (j + 0.5) / n

            punto = Point(lng, lat)

            # Solo incluir puntos que caen DENTRO del poligono
            if poligono.contains(punto):
                puntos_validos.append((lat, lng))

    # Si muy pocos puntos cayeron dentro agregar el centroide como minimo
    if len(puntos_validos) < 3:
        centroide = poligono.centroid
        puntos_validos.append((centroide.y, centroide.x))

    logger.info(
        f"Grilla generada: {len(puntos_validos)} puntos dentro del poligono "
        f"(grilla {n}x{n} para {superficie_ha} ha)"
    )

    return puntos_validos


def consultar_altitudes(puntos: list) -> list:
    """
    Consulta OpenTopoData NASA SRTM para una lista de puntos.
    OpenTopoData acepta hasta 100 puntos por peticion separados por |

    Args:
        puntos: Lista de tuplas (latitud, longitud)

    Returns:
        Lista de altitudes en el mismo orden que los puntos
    """
    locations = "|".join([f"{lat},{lng}" for lat, lng in puntos])

    try:
        url = f"{OPENTOPODATA_URL}/srtm30m"
        response = requests.get(
            url,
            params={"locations": locations},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if data.get('status') != 'OK' or not data.get('results'):
            logger.warning("OpenTopoData no retorno resultados validos")
            return []

        altitudes = [r['elevation'] for r in data['results']]
        return altitudes

    except requests.exceptions.Timeout:
        logger.warning("Timeout consultando OpenTopoData")
    except requests.exceptions.ConnectionError:
        logger.warning("Sin conexion a OpenTopoData")
    except Exception as e:
        logger.error(f"Error consultando OpenTopoData: {str(e)}")

    return []


def calcular_pendiente_horn(altitudes_grilla: dict) -> dict:
    """
    Calcula pendiente y orientacion usando el algoritmo de Horn (1981)
    aplicado al centroide de la grilla de puntos.
    """
    if not altitudes_grilla or len(altitudes_grilla) < 9:
        return {"pendiente_porcentaje": None, "orientacion": None}

    nombres = list(altitudes_grilla.keys())
    d = 0.0003 * 111320  # metros

    try:
        dzdx = (
            (altitudes_grilla.get('NE', 0) + 2 * altitudes_grilla.get('E', 0) + altitudes_grilla.get('SE', 0)) -
            (altitudes_grilla.get('NW', 0) + 2 * altitudes_grilla.get('W', 0) + altitudes_grilla.get('SW', 0))
        ) / (8 * d)

        dzdy = (
            (altitudes_grilla.get('NW', 0) + 2 * altitudes_grilla.get('N', 0) + altitudes_grilla.get('NE', 0)) -
            (altitudes_grilla.get('SW', 0) + 2 * altitudes_grilla.get('S', 0) + altitudes_grilla.get('SE', 0))
        ) / (8 * d)

        pendiente_rad = math.atan(math.sqrt(dzdx**2 + dzdy**2))
        pendiente_porcentaje = round(math.tan(pendiente_rad) * 100, 2)

        aspecto_rad = math.atan2(dzdy, -dzdx)
        aspecto_grados = math.degrees(aspecto_rad)
        if aspecto_grados < 0:
            aspecto_grados += 360

        if aspecto_grados < 22.5 or aspecto_grados >= 337.5:
            orientacion = 'norte'
        elif aspecto_grados < 67.5:
            orientacion = 'noreste'
        elif aspecto_grados < 112.5:
            orientacion = 'este'
        elif aspecto_grados < 157.5:
            orientacion = 'sureste'
        elif aspecto_grados < 202.5:
            orientacion = 'sur'
        elif aspecto_grados < 247.5:
            orientacion = 'suroeste'
        elif aspecto_grados < 292.5:
            orientacion = 'oeste'
        else:
            orientacion = 'noroeste'

        return {
            "pendiente_porcentaje": pendiente_porcentaje,
            "orientacion": orientacion
        }

    except Exception as e:
        logger.error(f"Error calculando pendiente Horn: {str(e)}")
        return {"pendiente_porcentaje": None, "orientacion": None}


def obtener_datos_topograficos_completos(
    coordenadas: list,
    superficie_ha: float
) -> dict:
    """
    Funcion principal que obtiene la topografia completa de una parcela.
    Genera grilla inteligente dentro del poligono, consulta NASA SRTM
    y calcula estadisticas de altitud, pendiente y orientacion.

    Args:
        coordenadas: Lista de pares [longitud, latitud] del poligono
        superficie_ha: Superficie calculada por PostGIS en hectareas

    Returns:
        Diccionario con todos los datos topograficos o None si falla
    """
    # Generar puntos dentro del poligono real
    puntos = generar_puntos_dentro_poligono(coordenadas, superficie_ha)

    if not puntos:
        logger.warning("No se generaron puntos dentro del poligono")
        return None

    # Consultar altitudes de todos los puntos
    altitudes = consultar_altitudes(puntos)

    if not altitudes:
        return None

    # Calcular estadisticas de altitud
    altitud_promedio = round(sum(altitudes) / len(altitudes), 1)
    altitud_minima = round(min(altitudes), 1)
    altitud_maxima = round(max(altitudes), 1)

    logger.info(
        f"Topografia completa: promedio={altitud_promedio} msnm "
        f"min={altitud_minima} max={altitud_maxima} "
        f"desnivel={altitud_maxima - altitud_minima}m "
        f"puntos={len(altitudes)}"
    )

    # Para la pendiente usamos la grilla de 9 puntos del centroide
    # porque Horn requiere una grilla regular
    centroide_lat = sum(p[0] for p in puntos) / len(puntos)
    centroide_lng = sum(p[1] for p in puntos) / len(puntos)

    d = 0.0003
    puntos_horn = {
        'NW': (centroide_lat + d, centroide_lng - d),
        'N':  (centroide_lat + d, centroide_lng),
        'NE': (centroide_lat + d, centroide_lng + d),
        'W':  (centroide_lat,     centroide_lng - d),
        'C':  (centroide_lat,     centroide_lng),
        'E':  (centroide_lat,     centroide_lng + d),
        'SW': (centroide_lat - d, centroide_lng - d),
        'S':  (centroide_lat - d, centroide_lng),
        'SE': (centroide_lat - d, centroide_lng + d),
    }

    altitudes_horn = consultar_altitudes(list(puntos_horn.values()))
    altitudes_horn_dict = {}
    if altitudes_horn:
        for nombre, altitud in zip(puntos_horn.keys(), altitudes_horn):
            altitudes_horn_dict[nombre] = altitud

    topografia = calcular_pendiente_horn(altitudes_horn_dict)

    return {
        "altitud_promedio_msnm": altitud_promedio,
        "altitud_minima_msnm": altitud_minima,
        "altitud_maxima_msnm": altitud_maxima,
        "pendiente_porcentaje": topografia["pendiente_porcentaje"],
        "orientacion": topografia["orientacion"],
        "num_puntos_consultados": len(altitudes)
    }


def calcular_centroide(coordenadas: list) -> tuple:
    """Calcula el centroide aproximado de un poligono."""
    latitudes = [punto[1] for punto in coordenadas]
    longitudes = [punto[0] for punto in coordenadas]
    return sum(latitudes) / len(latitudes), sum(longitudes) / len(longitudes)


def coordenadas_a_wkt(coordenadas: list) -> str:
    """Convierte coordenadas a formato WKT para PostGIS."""
    if coordenadas[0] != coordenadas[-1]:
        coordenadas = coordenadas + [coordenadas[0]]
    puntos_wkt = ", ".join([f"{p[0]} {p[1]}" for p in coordenadas])
    return f"POLYGON(({puntos_wkt}))"