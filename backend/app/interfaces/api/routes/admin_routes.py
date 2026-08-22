"""
Rutas HTTP del modulo de administracion,
Todos los endpoints aqui requieren autenticacion JWT
y que el usuario tenga rol de administrador (rol_id= 1)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.application.use_cases.administracion.gestionar_usuarios import GestionarUsuariosUseCase
from app.infrastructure.repositories.pg_usuario_repository import PgUsuarioRepository
from app.infrastructure.security.decorators import requiere_rol
from app.infrastructure.database import SessionLocal

admin_bp = Blueprint("admin", __name__)

def get_repo():
    """Fabrica que crea el repositorio con session de base de datos"""
    db = SessionLocal()
    return PgUsuarioRepository(db), db


def verificar_admin(usuario_id, repo)-> bool:
    """
    Verifica que el usuario que hace la peticion sea administrador. 
    Patron de autorizacion basado en el rol  -RBAC basico,
    EL rol_id 1 corresponde a administrador segun los datos inciiales
    """

    usuario = repo.buscar_por_id(usuario_id)
    return usuario and usuario.rol_id == 1


@admin_bp.route('/usuarios', methods=['GET'])
@jwt_required()
@requiere_rol('administrador')
def listar_usuarios():
    """
    GET /api/v1/admin/usuarios
    Lista todos los usuarios del sistema.
    Solo accesible por administradores.
    """

    usuario_id = get_jwt_identity()
    repo, db = get_repo()
    try: 
        if not verificar_admin(usuario_id, repo):
            return jsonify({"error": "Acceso denegado. Se requiere rol de administrador"}), 403
        
        use_case = GestionarUsuariosUseCase(repo)
        resultado = use_case.listar()
        return jsonify({"usuarios": resultado, "total": len(resultado)}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@admin_bp.route('/usuarios/<usuario_id>', methods=['GET'])
@jwt_required()
@requiere_rol('administrador')
def obtener_usuario(usuario_id):
    """
    GET /api/v1/admin/usuarios/<uuid>
    Retorna el detalle de un usuario especifico.
    """

    solicitante_id = get_jwt_identity()
    repo, db = get_repo()
    try: 
        if not verificar_admin(solicitante_id, repo):
            return jsonify({"error": "Acesso denegado"}), 403
        
        use_case = GestionarUsuariosUseCase(repo)
        resultado = use_case.obtener(usuario_id)
        return jsonify(resultado), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    finally: 
        db.close()


@admin_bp.route('/usuarios/<usuario_id>', methods=['PUT'])
@jwt_required()
@requiere_rol('administrador')
def editar_usuario(usuario_id):
    """
    PUT /api/v1/admin/usuarios/<uuid>
    Edita nombre y apellido de un usuario. 
    Body: {"nombre": "...", "apellido": "..."}
    """

    solicitante_id = get_jwt_identity()
    repo, db = get_repo()
    try: 
        if not verificar_admin(solicitante_id, repo):
            return jsonify({"error": "Acceso denegado"}), 403
        
        datos = request.get_json()
        if not datos or not datos.get('nombre') or not datos.get('apellido'):
            return jsonify({"error": "Nombre y Apellido son requeridos"}), 400
        
        use_case = GestionarUsuariosUseCase(repo)
        resultado = use_case.editar(usuario_id, datos['nombre'], datos['apellido'])
        return jsonify(resultado), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    finally: 
        db.close()

@admin_bp.route('/usuarios/<usuario_id>/estado', methods=['PATCH'])
@jwt_required()
@requiere_rol('administrador')
def cambiar_estado_usuario(usuario_id):
    """
    PATCH /api/v1/admin/usuarios/<uuid>/estado
    Activa o desactiva un usuario.
    Body: { "activo": true } o { "activo": false }
    Usamos PATCH y no PUT porque solo cambiamos un campo específico. 
    """

    solicitante_id = get_jwt_identity()
    repo, db = get_repo()
    try:
        if not verificar_admin(solicitante_id, repo):
            return jsonify({"error": "Acceso denegado"}),403
        
        datos = request.get_json()
        if datos is None or 'activo' not in datos:
            return jsonify({"error": "El campo activo es requerido"}), 400
        
        use_case = GestionarUsuariosUseCase(repo)
        resultado = use_case.cambiar_estado(usuario_id, datos['activo'])
        return jsonify(resultado), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    finally:
        db.close()