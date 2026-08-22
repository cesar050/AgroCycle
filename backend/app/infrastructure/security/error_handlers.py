"""
Manejadores globales de errores para AgroCycle.

Centraliza todas las respuestas de error en un formato
consistente. Sin esto Flask retorna HTML para errores 404
y 500 — inaceptable para una API REST.

Formato estándar de error:
{
    "error": "Descripción del error",
    "codigo": 404,
    "sistema": "AgroCycle"
}
"""
from flask import Flask, jsonify
from flask_jwt_extended.exceptions import NoAuthorizationError, InvalidHeaderError
from jwt.exceptions import ExpiredSignatureError


def registrar_error_handlers(app: Flask) -> None:
    """Registra todos los manejadores de error en la app Flask."""

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({
            'error': 'Solicitud incorrecta. Verifica los datos enviados.',
            'codigo': 400,
            'sistema': 'AgroCycle'
        }), 400

    @app.errorhandler(401)
    def no_autorizado(e):
        return jsonify({
            'error': 'No autorizado. Inicia sesión para continuar.',
            'codigo': 401,
            'sistema': 'AgroCycle'
        }), 401

    @app.errorhandler(403)
    def prohibido(e):
        return jsonify({
            'error': 'Acceso denegado. No tienes permisos para esta acción.',
            'codigo': 403,
            'sistema': 'AgroCycle'
        }), 403

    @app.errorhandler(404)
    def no_encontrado(e):
        return jsonify({
            'error': 'Recurso no encontrado.',
            'codigo': 404,
            'sistema': 'AgroCycle'
        }), 404

    @app.errorhandler(405)
    def metodo_no_permitido(e):
        return jsonify({
            'error': 'Método HTTP no permitido para este endpoint.',
            'codigo': 405,
            'sistema': 'AgroCycle'
        }), 405

    @app.errorhandler(429)
    def demasiadas_solicitudes(e):
        return jsonify({
            'error': 'Demasiadas solicitudes. Espera un momento antes de intentar de nuevo.',
            'codigo': 429,
            'sistema': 'AgroCycle'
        }), 429

    @app.errorhandler(500)
    def error_interno(e):
        app.logger.error(f'Error interno del servidor: {str(e)}')
        return jsonify({
            'error': 'Error interno del servidor. El equipo ha sido notificado.',
            'codigo': 500,
            'sistema': 'AgroCycle'
        }), 500

    @app.errorhandler(NoAuthorizationError)
    def jwt_no_autorizado(e):
        return jsonify({
            'error': 'Token de autenticación no proporcionado.',
            'codigo': 401,
            'sistema': 'AgroCycle'
        }), 401

    @app.errorhandler(ExpiredSignatureError)
    def jwt_expirado(e):
        return jsonify({
            'error': 'Tu sesión ha expirado. Inicia sesión nuevamente.',
            'codigo': 401,
            'sistema': 'AgroCycle'
        }), 401