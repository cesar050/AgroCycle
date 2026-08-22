from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app.application.use_cases.estimacion.generar_estimacion import GenerarEstimacionUseCase
from app.infrastructure.repositories.pg_estimacion_repository import PgEstimacionRepository
from app.infrastructure.repositories.pg_temporada_parcela_repository import PgTemporadaParcelaRepository
from app.infrastructure.database import get_db
from app.infrastructure.security.decorators import requiere_rol

estimacion_bp = Blueprint('estimacion', __name__)


@estimacion_bp.route('/temporada-parcela/<tp_id>/estimar', methods=['POST'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def generar_estimacion(tp_id):
    claims = get_jwt()
    agricultor_id = claims.get('sub')
    db = next(get_db())

    use_case = GenerarEstimacionUseCase(
        db=db,
        estimacion_repo=PgEstimacionRepository(db),
        temporada_parcela_repo=PgTemporadaParcelaRepository(db),
    )

    resultado, status = use_case.ejecutar(
        temporada_parcela_id=tp_id,
        agricultor_id=agricultor_id,
    )
    return jsonify(resultado), status


@estimacion_bp.route('/temporada-parcela/<tp_id>/estimaciones', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def historial_estimaciones(tp_id):
    db = next(get_db())
    repo = PgEstimacionRepository(db)
    estimaciones = repo.listar_por_temporada_parcela(tp_id)

    return jsonify({
        'temporada_parcela_id': tp_id,
        'total': len(estimaciones),
        'estimaciones': [
            {
                'id': e.id,
                'valor_qq_ha': e.valor_qq_ha,
                'valor_total_qq': e.valor_total_qq,
                'rango_minimo_qq_ha': e.valor_minimo_qq_ha,
                'rango_maximo_qq_ha': e.valor_maximo_qq_ha,
                'margen_error_porcentaje': e.margen_error_porcentaje,
                'algoritmo_usado': e.algoritmo_usado,
                'etapa_fenologica_momento': e.etapa_fenologica_momento,
                'dias_desde_siembra_momento': e.dias_desde_siembra_momento,
                'factores_positivos': e.factores_positivos,
                'factores_negativos': e.factores_negativos,
                'fecha_generacion': e.fecha_generacion.isoformat() if e.fecha_generacion else None,
            }
            for e in estimaciones
        ]
    }), 200


@estimacion_bp.route('/temporada/<temporada_id>/estimaciones', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def estimaciones_por_temporada(temporada_id):
    db = next(get_db())
    repo = PgEstimacionRepository(db)
    estimaciones = repo.listar_por_temporada(temporada_id)

    total_qq = sum(
        e.valor_total_qq for e in estimaciones if e.valor_total_qq
    )

    return jsonify({
        'temporada_id': temporada_id,
        'total_parcelas': len(estimaciones),
        'produccion_total_estimada_qq': round(total_qq, 2),
        'parcelas': [
            {
                'id': e.id,
                'temporada_parcela_id': e.temporada_parcela_id,
                'valor_qq_ha': e.valor_qq_ha,
                'valor_total_qq': e.valor_total_qq,
                'margen_error_porcentaje': e.margen_error_porcentaje,
                'algoritmo_usado': e.algoritmo_usado,
                'etapa_fenologica_momento': e.etapa_fenologica_momento,
                'fecha_generacion': e.fecha_generacion.isoformat() if e.fecha_generacion else None,
            }
            for e in estimaciones
        ]
    }), 200