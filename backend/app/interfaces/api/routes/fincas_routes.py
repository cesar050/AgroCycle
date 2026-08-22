"""
Rutas HTTP del modulo de Gestion de Fincas.
Todos los endpoints requieren JWT valido.
El agricultor_id se obtiene directamente del JWT enriquecido.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.application.use_cases.fincas_parcelas.registrar_finca import RegistrarFincaUseCase
from app.application.use_cases.fincas_parcelas.gestionar_fincas import GestionarFincasUseCase
from app.infrastructure.repositories.pg_finca_repository import PgFincaRepository
from app.infrastructure.security.decorators import requiere_rol
from app.infrastructure.database import SessionLocal

fincas_bp = Blueprint('fincas', __name__)


def get_repos():
    """
    Crea el repositorio de fincas con su sesion de base de datos.
    """
    db = SessionLocal()
    return PgFincaRepository(db), db


def obtener_agricultor_id() -> str:
    """
    Obtiene el agricultor_id directamente del JWT enriquecido.
    El login ya incluyo el perfil_id en el token.
    No necesita consultar la base de datos.
    """
    claims = get_jwt()
    perfil_id = claims.get('perfil_id')
    if not perfil_id:
        raise PermissionError("El usuario no tiene perfil de agricultor")
    return perfil_id


@fincas_bp.route('', methods=['POST'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def registrar_finca():
    """
    POST /api/v1/fincas
    Registra una nueva finca para el agricultor autenticado.
    Body: { "nombre": "Finca La Esperanza", "provincia": "Loja",
            "canton": "Paltas", "parroquia": "Guachanama",
            "sector": "Bramaderos", "descripcion": "..." }
    """
    usuario_id = get_jwt_identity()
    datos = request.get_json()

    if not datos or not datos.get('nombre'):
        return jsonify({"error": "El nombre de la finca es requerido"}), 400

    finca_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = RegistrarFincaUseCase(finca_repo)
        resultado = use_case.ejecutar(
            agricultor_id=agricultor_id,
            nombre=datos['nombre'],
            coordenadas=datos.get('coordenadas'),
            provincia=datos.get('provincia'),
            canton=datos.get('canton'),
            parroquia=datos.get('parroquia'),
            sector=datos.get('sector'),
            descripcion=datos.get('descripcion')
        )
        return jsonify(resultado), 201

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    finally:
        db.close()


@fincas_bp.route('', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def listar_fincas():
    """
    GET /api/v1/fincas
    Lista todas las fincas activas del agricultor autenticado.
    """
    usuario_id = get_jwt_identity()
    finca_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = GestionarFincasUseCase(finca_repo)
        resultado = use_case.listar(agricultor_id)
        return jsonify({"fincas": resultado, "total": len(resultado)}), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@fincas_bp.route('/<finca_id>', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def obtener_finca(finca_id):
    """
    GET /api/v1/fincas/<uuid>
    Retorna el detalle de una finca especifica.
    """
    usuario_id = get_jwt_identity()
    finca_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = GestionarFincasUseCase(finca_repo)
        resultado = use_case.obtener(finca_id, agricultor_id)
        return jsonify(resultado), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    finally:
        db.close()


@fincas_bp.route('/<finca_id>', methods=['PUT'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def editar_finca(finca_id):
    """
    PUT /api/v1/fincas/<uuid>
    Edita los datos de una finca.
    """
    usuario_id = get_jwt_identity()
    datos = request.get_json()

    if not datos:
        return jsonify({"error": "No se recibieron datos"}), 400

    finca_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = GestionarFincasUseCase(finca_repo)
        resultado = use_case.editar(finca_id, agricultor_id, datos)
        return jsonify(resultado), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    finally:
        db.close()