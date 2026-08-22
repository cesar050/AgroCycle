"""
Configuración CORS restrictiva para AgroCycle.

CORS (Cross-Origin Resource Sharing) controla qué dominios
pueden hacer peticiones al API. Sin esto cualquier página web
podría llamar al API con las credenciales del usuario.

En desarrollo: permite localhost:4200 (Angular) e Insomnia.
En producción: solo el dominio real de AgroCycle.
"""
from flask import Flask
from flask_cors import CORS


def configurar_cors(app: Flask) -> None:
    """
    Configura CORS según el entorno de ejecución.
    Reemplaza el CORS(app) genérico del main.py.
    """
    entorno = app.config.get('FLASK_ENV', 'development')

    if entorno == 'production':
        # Solo el frontend Angular en producción
        origenes_permitidos = [
            'https://agrocycle.ec',
            'https://www.agrocycle.ec',
        ]
    else:
        # Desarrollo: Angular local e Insomnia
        origenes_permitidos = [
            'http://localhost:4200',
            'http://127.0.0.1:4200',
            'http://localhost:3000',
        ]

    CORS(
        app,
        resources={
            r'/api/*': {
                'origins': origenes_permitidos,
                'methods': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
                'allow_headers': [
                    'Content-Type',
                    'Authorization',
                    'X-Requested-With',
                ],
                # Permite enviar cookies y headers de autenticación
                'supports_credentials': True,
                'max_age': 600,
            }
        }
    )