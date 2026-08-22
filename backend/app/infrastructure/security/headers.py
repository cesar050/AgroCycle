"""
Headers de seguridad HTTP para AgroCycle.

Estos headers le dicen al navegador cómo comportarse
para proteger al usuario de ataques comunes:

- CSP: solo permite cargar recursos del propio dominio
- HSTS: fuerza HTTPS en producción
- X-Frame-Options: evita clickjacking (la app no puede
  ser embebida en un iframe de otro sitio)
- X-Content-Type-Options: evita que el navegador adivine
  el tipo de contenido (MIME sniffing)
"""
from flask import Flask


def configurar_headers_seguridad(app: Flask) -> None:
    """
    Registra un after_request que agrega headers de seguridad
    a todas las respuestas del servidor automáticamente.
    """

    @app.after_request
    def agregar_headers(response):
        entorno = app.config.get('FLASK_ENV', 'development')

        # Content Security Policy
        # En desarrollo es permisivo para que Insomnia funcione.
        # En producción solo permite el dominio de Angular.
        if entorno == 'production':
            csp = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "connect-src 'self';"
            )
        else:
            csp = "default-src *; script-src * 'unsafe-inline';"

        response.headers['Content-Security-Policy'] = csp

        # Evita que el navegador adivine el tipo de contenido
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Evita que la app sea embebida en un iframe externo
        response.headers['X-Frame-Options'] = 'DENY'

        # Fuerza HTTPS solo en producción
        if entorno == 'production':
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains'
            )

        # Oculta que el servidor es Flask/Python
        response.headers['Server'] = 'AgroCycle'

        # Evita que el navegador almacene respuestas del API en caché
        response.headers['Cache-Control'] = (
            'no-store, no-cache, must-revalidate, max-age=0'
        )
        response.headers['Pragma'] = 'no-cache'

        return response