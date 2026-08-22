"""
Rate limiting para AgroCycle usando Redis como backend.

Protege contra:
- Ataques de fuerza bruta en login
- Scraping masivo de datos
- Abuso de endpoints costosos (clima, PDF, estimación)

Los límites son por IP para endpoints públicos y por
usuario autenticado para endpoints privados.

Estrategia de límites:
- Login: muy restrictivo — 5 intentos por minuto
- Registro: restrictivo — 3 por hora
- Endpoints costosos (PDF, estimación): moderado — 10 por hora
- Endpoints normales: permisivo — 100 por minuto
"""
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os


# Instancia global para importar en las rutas
# La URI se configura en inicializar_limiter()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=['200 per minute', '2000 per hour'],
    storage_uri=os.getenv('REDIS_URL', 'redis://redis:6380/0'),
)


def inicializar_limiter(app: Flask) -> None:
    """
    Inicializa el limiter con la app Flask.
    Se llama desde create_app() en main.py.
    """
    limiter.init_app(app)