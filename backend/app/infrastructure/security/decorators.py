"""
Decoradores de autorizacion para AgroCycle.
Usan el rol incluido en el JWT para verificar permisos 
antes de ejecutar cualquier endpoint protegido.
Patron Decorator aplicado a la seguridad 
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt

def requiere_rol(*roles_permitidos):
    """
    Decorator que verifica que el usuario tenga el rol requerido.
    Uso:
        @requiere_rol('agricultor')
        @jwt_required()
        def mi_endpoint():
            ...
    Los roles disponibles son: administrador, agricultor, agronomo 
    Se pueden pasar multiples roles si el endpoint acepta varios:
        @requiere_rol('administrador', 'agronomo')
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            rol_usuario = claims.get('rol')

            # Mapa de rol_id a nombre rol
            roles = {
                1: 'administrador',
                2: 'agricultor',
                3: 'agronomo'
            }

            nombre_rol = roles.get(rol_usuario, 'desconocido')

            if nombre_rol not in roles_permitidos:
                return jsonify({
                    "error": f"Acceso denegado. Se requiere rol: {', '.join(roles_permitidos)}"
                }),403
            return func(*args, **kwargs)
        return wrapper
    return decorator