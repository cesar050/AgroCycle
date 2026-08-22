"""
Rutas del módulo agrónomo de AgroCycle.
Gestiona observaciones técnicas, recomendaciones y evaluaciones de campo.
"""
from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from app.application.use_cases.agronomo.registrar_observacion import RegistrarObservacionUseCase
from app.application.use_cases.agronomo.registrar_recomendacion import RegistrarRecomendacionUseCase
from app.application.use_cases.agronomo.registrar_evaluacion_campo import RegistrarEvaluacionCampoUseCase
from app.infrastructure.repositories.pg_observacion_repository import PgObservacionRepository
from app.infrastructure.repositories.pg_recomendacion_repository import PgRecomendacionRepository
from app.infrastructure.repositories.pg_evaluacion_campo_repository import PgEvaluacionCampoRepository
from app.infrastructure.database import get_db
from app.infrastructure.security.decorators import requiere_rol

agronomo_bp = Blueprint('agronomo', __name__)


@agronomo_bp.route('/temporadas/<temporada_id>/observaciones', methods=['POST'])
@jwt_required()
@requiere_rol('agronomo', 'administrador')
def registrar_observacion(temporada_id):
    """
    CU-AGR-003 — Registra una observación técnica del agrónomo.

    Body JSON esperado:
    {
        "tipo": "cultivo",
        "descripcion": "Plantas con amarillamiento en hojas inferiores",
        "fecha": "2026-02-15",
        "temporada_parcela_id": null
    }
    """
    claims = get_jwt()
    agronomo_usuario_id = claims.get('sub')
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Body JSON requerido'}), 400

    campos_requeridos = ['tipo', 'descripcion', 'fecha']
    for campo in campos_requeridos:
        if campo not in data:
            return jsonify({
                'error': f"Campo requerido faltante: {campo}"
            }), 400

    try:
        fecha = date.fromisoformat(data['fecha'])
    except ValueError:
        return jsonify({
            'error': 'Formato de fecha inválido. Use YYYY-MM-DD'
        }), 400

    db = next(get_db())
    use_case = RegistrarObservacionUseCase(
        db=db,
        observacion_repo=PgObservacionRepository(db),
    )

    resultado, status = use_case.ejecutar(
        agronomo_usuario_id=agronomo_usuario_id,
        temporada_id=temporada_id,
        tipo=data['tipo'],
        descripcion=data['descripcion'],
        fecha=fecha,
        temporada_parcela_id=data.get('temporada_parcela_id'),
    )
    return jsonify(resultado), status


@agronomo_bp.route('/temporadas/<temporada_id>/observaciones', methods=['GET'])
@jwt_required()
@requiere_rol('agronomo', 'agricultor', 'administrador')
def listar_observaciones(temporada_id):
    """
    Lista todas las observaciones técnicas de una temporada.
    Visible para el agrónomo y el agricultor vinculado.
    """
    db = next(get_db())
    repo = PgObservacionRepository(db)
    observaciones = repo.listar_por_temporada(temporada_id)

    return jsonify({
        'temporada_id': temporada_id,
        'total': len(observaciones),
        'observaciones': [
            {
                'id': o.id,
                'tipo': o.tipo,
                'descripcion': o.descripcion,
                'fecha': str(o.fecha),
                'temporada_parcela_id': o.temporada_parcela_id,
                'es_general': o.es_general(),
                'agronomo_id': o.agronomo_id,
            }
            for o in observaciones
        ]
    }), 200


@agronomo_bp.route('/temporadas/<temporada_id>/recomendaciones', methods=['POST'])
@jwt_required()
@requiere_rol('agronomo', 'administrador')
def registrar_recomendacion(temporada_id):
    """
    CU-AGR-004 — Registra una recomendación agronómica al agricultor.

    Body JSON esperado:
    {
        "descripcion": "Aplicar fertilización nitrogenada de emergencia",
        "urgencia": "alta",
        "fecha": "2026-02-15",
        "tipo": "fertilizacion",
        "fecha_limite": "2026-02-18",
        "temporada_parcela_id": null
    }
    """
    claims = get_jwt()
    agronomo_usuario_id = claims.get('sub')
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Body JSON requerido'}), 400

    campos_requeridos = ['descripcion', 'urgencia', 'fecha']
    for campo in campos_requeridos:
        if campo not in data:
            return jsonify({
                'error': f"Campo requerido faltante: {campo}"
            }), 400

    try:
        fecha = date.fromisoformat(data['fecha'])
        fecha_limite = (
            date.fromisoformat(data['fecha_limite'])
            if data.get('fecha_limite') else None
        )
    except ValueError:
        return jsonify({
            'error': 'Formato de fecha inválido. Use YYYY-MM-DD'
        }), 400

    db = next(get_db())
    use_case = RegistrarRecomendacionUseCase(
        db=db,
        recomendacion_repo=PgRecomendacionRepository(db),
    )

    resultado, status = use_case.ejecutar(
        agronomo_usuario_id=agronomo_usuario_id,
        temporada_id=temporada_id,
        descripcion=data['descripcion'],
        urgencia=data['urgencia'],
        fecha=fecha,
        tipo=data.get('tipo'),
        temporada_parcela_id=data.get('temporada_parcela_id'),
        fecha_limite=fecha_limite,
    )
    return jsonify(resultado), status


@agronomo_bp.route('/temporadas/<temporada_id>/recomendaciones', methods=['GET'])
@jwt_required()
@requiere_rol('agronomo', 'agricultor', 'administrador')
def listar_recomendaciones(temporada_id):
    """
    Lista recomendaciones de una temporada ordenadas por urgencia.
    Las urgentes aparecen siempre primero.
    """
    db = next(get_db())
    repo = PgRecomendacionRepository(db)
    recomendaciones = repo.listar_por_temporada(temporada_id)

    return jsonify({
        'temporada_id': temporada_id,
        'total': len(recomendaciones),
        'recomendaciones': [
            {
                'id': r.id,
                'tipo': r.tipo,
                'descripcion': r.descripcion,
                'urgencia': r.urgencia,
                'es_urgente': r.es_urgente(),
                'fecha': str(r.fecha),
                'fecha_limite': str(r.fecha_limite) if r.fecha_limite else None,
                'leida': r.leida,
                'implementada': r.implementada,
                'temporada_parcela_id': r.temporada_parcela_id,
            }
            for r in recomendaciones
        ]
    }), 200


@agronomo_bp.route('/recomendaciones/<recomendacion_id>/leer', methods=['PATCH'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def marcar_recomendacion_leida(recomendacion_id):
    """
    El agricultor marca una recomendación como leída.
    Actualiza el badge de notificaciones en su dashboard.
    """
    db = next(get_db())
    repo = PgRecomendacionRepository(db)
    actualizada = repo.marcar_leida(recomendacion_id)

    if not actualizada:
        return jsonify({
            'error': 'Recomendación no encontrada'
        }), 404

    return jsonify({
        'mensaje': 'Recomendación marcada como leída',
        'recomendacion_id': recomendacion_id,
    }), 200


@agronomo_bp.route('/temporadas/<temporada_id>/evaluaciones', methods=['POST'])
@jwt_required()
@requiere_rol('agronomo', 'administrador')
def registrar_evaluacion_campo(temporada_id):
    """
    CU-AGR-007 — Registra evaluación de campo presencial.

    Body JSON esperado:
    {
        "fecha": "2026-02-15",
        "temporada_parcela_id": "uuid-opcional",
        "densidad_plantas_ha": 52000,
        "incidencia_plagas_porcentaje": 5.0,
        "incidencia_enfermedades_porcentaje": 0.0,
        "estado_nutricional": "bueno",
        "estado_fenologico_confirmado": "floracion",
        "observaciones": "Cultivo en buen estado general"
    }
    """
    claims = get_jwt()
    agronomo_usuario_id = claims.get('sub')
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Body JSON requerido'}), 400

    if 'fecha' not in data:
        return jsonify({'error': 'Campo requerido faltante: fecha'}), 400

    try:
        fecha = date.fromisoformat(data['fecha'])
    except ValueError:
        return jsonify({
            'error': 'Formato de fecha inválido. Use YYYY-MM-DD'
        }), 400

    db = next(get_db())
    use_case = RegistrarEvaluacionCampoUseCase(
        db=db,
        evaluacion_repo=PgEvaluacionCampoRepository(db),
    )

    resultado, status = use_case.ejecutar(
        agronomo_usuario_id=agronomo_usuario_id,
        temporada_id=temporada_id,
        fecha=fecha,
        temporada_parcela_id=data.get('temporada_parcela_id'),
        densidad_plantas_ha=data.get('densidad_plantas_ha'),
        incidencia_plagas_porcentaje=data.get('incidencia_plagas_porcentaje'),
        incidencia_enfermedades_porcentaje=data.get('incidencia_enfermedades_porcentaje'),
        estado_nutricional=data.get('estado_nutricional'),
        estado_fenologico_confirmado=data.get('estado_fenologico_confirmado'),
        observaciones=data.get('observaciones'),
    )
    return jsonify(resultado), status


@agronomo_bp.route('/temporadas/<temporada_id>/evaluaciones', methods=['GET'])
@jwt_required()
@requiere_rol('agronomo', 'agricultor', 'administrador')
def listar_evaluaciones(temporada_id):
    """
    Lista evaluaciones de campo de una temporada en orden cronológico.
    Permite ver la evolución del cultivo durante la temporada.
    """
    db = next(get_db())
    repo = PgEvaluacionCampoRepository(db)
    evaluaciones = repo.listar_por_temporada(temporada_id)

    return jsonify({
        'temporada_id': temporada_id,
        'total': len(evaluaciones),
        'evaluaciones': [
            {
                'id': e.id,
                'fecha': str(e.fecha),
                'temporada_parcela_id': e.temporada_parcela_id,
                'densidad_plantas_ha': e.densidad_plantas_ha,
                'incidencia_plagas_porcentaje': e.incidencia_plagas_porcentaje,
                'incidencia_enfermedades_porcentaje': e.incidencia_enfermedades_porcentaje,
                'estado_nutricional': e.estado_nutricional,
                'estado_fenologico_confirmado': e.estado_fenologico_confirmado,
                'observaciones': e.observaciones,
                'alerta_generada': e.alerta_generada,
            }
            for e in evaluaciones
        ]
    }), 200