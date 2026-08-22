"""
Rutas HTTP del modulo de Actividades Agricolas.
Permite registrar y listar actividades de una temporada.
Los riegos se registran aqui y ajustan automaticamente
el balance hidrico FAO-56.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from datetime import date
from sqlalchemy import text
from app.application.use_cases.actividades.registrar_actividad import RegistrarActividadUseCase
from app.application.use_cases.actividades.listar_actividades import ListarActividadesUseCase
from app.application.use_cases.actividades.eliminar_actividad import EliminarActividadUseCase
from app.infrastructure.repositories.pg_actividad_repository import PgActividadRepository
from app.infrastructure.repositories.pg_dato_climatico_repository import PgDatoClimaticoRepository
from app.infrastructure.database import SessionLocal
from app.infrastructure.security.decorators import requiere_rol

actividades_bp = Blueprint('actividades', __name__)


def get_db():
    return SessionLocal()


def obtener_usuario_id() -> str:
    return get_jwt_identity()


def obtener_agricultor_id() -> str:
    claims = get_jwt()
    perfil_id = claims.get('perfil_id')
    if not perfil_id:
        raise PermissionError("El usuario no tiene perfil de agricultor")
    return perfil_id


@actividades_bp.route('/temporadas/<temporada_id>/actividades', methods=['POST'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def registrar_actividad(temporada_id):
    """
    POST /api/v1/actividades/temporadas/<uuid>/actividades
    Registra una nueva actividad agricola.
    Body: {
        "temporada_parcela_id": "uuid",
        "parcela_id": "uuid",
        "tipo_actividad_id": 5,
        "fecha": "2026-01-15",
        "descripcion": "Riego por acequia sector norte",
        "costo_total": 0,
        "tipo_riego": "perdido",
        "duracion_horas": 3,
        "porcentaje_parcela_regada": 60
    }
    """
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "No se recibieron datos"}), 400

    campos_requeridos = ['temporada_parcela_id', 'tipo_actividad_id', 'fecha']
    for campo in campos_requeridos:
        if not datos.get(campo):
            return jsonify({"error": f"El campo {campo} es requerido"}), 400

    db = get_db()
    try:
        usuario_id = obtener_usuario_id()
        actividad_repo = PgActividadRepository(db)
        clima_repo = PgDatoClimaticoRepository(db)

        use_case = RegistrarActividadUseCase(actividad_repo, clima_repo, db)
        resultado = use_case.ejecutar(
            temporada_id=temporada_id,
            temporada_parcela_id=datos['temporada_parcela_id'],
            tipo_actividad_id=datos['tipo_actividad_id'],
            fecha=date.fromisoformat(datos['fecha']),
            usuario_id=usuario_id,
            descripcion=datos.get('descripcion'),
            observaciones=datos.get('observaciones'),
            costo_total=datos.get('costo_total', 0),
            parcela_id=datos.get('parcela_id'),
            tipo_riego=datos.get('tipo_riego'),
            duracion_horas=datos.get('duracion_horas'),
            porcentaje_parcela_regada=datos.get('porcentaje_parcela_regada', 100),
            insumo_id=datos.get('insumo_id'),
            insumo_personalizado=datos.get('insumo_personalizado'),
            dosis_kg_ha=datos.get('dosis_kg_ha'),
            metodo_aplicacion=datos.get('metodo_aplicacion'),
            costo_unitario=datos.get('costo_unitario'),
            tipo_control=datos.get('tipo_control'),
            dosis_aplicada=datos.get('dosis_aplicada'),
            motivo=datos.get('motivo'),
            incidencia_porcentaje=datos.get('incidencia_porcentaje'),
            condicion_humedad_momento=datos.get('condicion_humedad_momento'),
            condicion_temperatura_momento=datos.get('condicion_temperatura_momento'),
            efectividad_observada=datos.get('efectividad_observada'),
            tipo_labor=datos.get('tipo_labor'),
            numero_personas=datos.get('numero_personas', 1),
            dias_trabajados=datos.get('dias_trabajados'),
            costo_jornal=datos.get('costo_jornal'),
            es_mano_obra_propia=datos.get('es_mano_obra_propia', False)
        )
        return jsonify(resultado), 201

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@actividades_bp.route('/temporadas/<temporada_id>/actividades', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def listar_actividades(temporada_id):
    """
    GET /api/v1/actividades/temporadas/<uuid>/actividades
    Lista todas las actividades de una temporada.
    Query param opcional: temporada_parcela_id
    """
    temporada_parcela_id = request.args.get('temporada_parcela_id')

    db = get_db()
    try:
        actividad_repo = PgActividadRepository(db)
        use_case = ListarActividadesUseCase(actividad_repo, db)
        resultado = use_case.ejecutar(temporada_id, temporada_parcela_id)

        return jsonify({
            "temporada_id": temporada_id,
            "actividades": resultado,
            "total": len(resultado)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@actividades_bp.route('/tipos', methods=['GET'])
@jwt_required()
def listar_tipos_actividad():
    """
    GET /api/v1/actividades/tipos
    Lista todos los tipos de actividad disponibles.
    """
    db = get_db()
    try:
        resultados = db.execute(
            text("SELECT id, nombre, descripcion FROM tipos_actividad WHERE activo = true ORDER BY id")
        ).fetchall()

        return jsonify({
            "tipos": [
                {
                    "id": r.id,
                    "nombre": r.nombre,
                    "descripcion": r.descripcion
                }
                for r in resultados
            ]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@actividades_bp.route('/<actividad_id>', methods=['DELETE'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def eliminar_actividad(actividad_id):
    """
    CU-ACT-007 — Soft delete de una actividad.
    La actividad queda marcada como inactiva pero no se borra.
    Solo disponible mientras la temporada esté activa.
    """
    claims = get_jwt()
    agricultor_id = claims.get('sub')

    db = get_db()
    use_case = EliminarActividadUseCase(db=db)

    resultado, status = use_case.ejecutar(
        actividad_id=actividad_id,
        agricultor_id=agricultor_id,
    )
    return jsonify(resultado), status