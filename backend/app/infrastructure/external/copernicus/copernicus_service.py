"""
Servicio de consulta de NDVI via Copernicus Data Space Ecosystem (CDSE).
Usa Sentinel-2 L2A a traves del WMS de Sentinel Hub para obtener
una imagen NDVI recortada al area de la finca.

Requiere:
- COPERNICUS_USERNAME / COPERNICUS_PASSWORD: credenciales de la
  cuenta CDSE (gratuita, dataspace.copernicus.eu).
- COPERNICUS_WMS_INSTANCE_ID: id de una configuracion de Sentinel Hub
  creada en el dashboard de la cuenta CDSE con una capa NDVI. No se
  deriva de usuario/contrasena, hay que crearla aparte.
"""
import requests
import os
import time
from app.infrastructure.logging.logger import configurar_logger

logger = configurar_logger('copernicus_service')

COPERNICUS_TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/"
    "protocol/openid-connect/token"
)

# Cache en memoria del token de acceso para no pedir uno nuevo
# en cada request. Se invalida 30s antes de su expiracion real.
_token_cache: dict = {}


def obtener_token() -> str | None:
    """
    Obtiene (o reutiliza del cache) un access_token de Copernicus
    Data Space Ecosystem via OAuth2 password grant.
    Retorna None si faltan credenciales o si falla la autenticacion.
    """
    ahora = time.time()
    if _token_cache.get('access_token') and _token_cache.get('expires_at', 0) > ahora:
        return _token_cache['access_token']

    username = os.getenv('COPERNICUS_USERNAME')
    password = os.getenv('COPERNICUS_PASSWORD')
    if not username or not password:
        logger.warning(
            "COPERNICUS_USERNAME/COPERNICUS_PASSWORD no configurados"
        )
        return None

    try:
        response = requests.post(
            COPERNICUS_TOKEN_URL,
            data={
                "grant_type": "password",
                "client_id": "cdse-public",
                "username": username,
                "password": password,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        access_token = data.get('access_token')
        if not access_token:
            logger.warning("Copernicus no retorno access_token")
            return None

        expires_in = data.get('expires_in', 0)
        _token_cache['access_token'] = access_token
        _token_cache['expires_at'] = ahora + max(expires_in - 30, 0)

        return access_token

    except requests.exceptions.Timeout:
        logger.warning("Timeout obteniendo token de Copernicus")
    except requests.exceptions.ConnectionError:
        logger.warning("Sin conexion a Copernicus identity")
    except Exception as e:
        logger.error(f"Error obteniendo token de Copernicus: {str(e)}")

    return None


def obtener_ndvi_bbox(bbox: tuple, fecha: str) -> bytes | None:
    """
    Pide imagen NDVI de Sentinel-2 L2A via WMS de Copernicus.

    Args:
        bbox: (min_lng, min_lat, max_lng, max_lat)
        fecha: 'YYYY-MM-DD' - usa TIME=fecha/fecha

    Returns:
        Bytes de la imagen PNG, o None si falla.
    """
    token = obtener_token()
    if not token:
        return None

    instance_id = os.getenv('COPERNICUS_WMS_INSTANCE_ID')
    if not instance_id:
        logger.warning(
            "COPERNICUS_WMS_INSTANCE_ID no configurado, no se puede pedir NDVI"
        )
        return None

    min_lng, min_lat, max_lng, max_lat = bbox

    try:
        url = f"https://sh.dataspace.copernicus.eu/wms/{instance_id}"
        params = {
            "SERVICE": "WMS",
            "REQUEST": "GetMap",
            "VERSION": "1.3.0",
            "LAYERS": "VEGETATION_INDEX",
            "STYLES": "",
            "CRS": "EPSG:4326",
            # WMS 1.3.0 + EPSG:4326 usa orden lat,lng
            "BBOX": f"{min_lat},{min_lng},{max_lat},{max_lng}",
            "WIDTH": 512,
            "HEIGHT": 512,
            "FORMAT": "image/png",
            "TIME": f"{fecha}/{fecha}",
        }
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(url, params=params, headers=headers, timeout=30)
        logger.debug(
            f"WMS response status={response.status_code} size={len(response.content)}B"
        )
        if response.status_code >= 400:
            logger.warning(f"WMS response body: {response.text[:1000]}")
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            logger.warning(
                f"Copernicus WMS no devolvio una imagen "
                f"(content-type={content_type}) para bbox={bbox} fecha={fecha}"
            )
            return None

        return response.content

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout consultando NDVI para bbox={bbox} fecha={fecha}")
    except requests.exceptions.ConnectionError:
        logger.warning(f"Sin conexion a Copernicus WMS para bbox={bbox}")
    except Exception as e:
        logger.error(f"Error consultando NDVI: {str(e)}")

    return None
