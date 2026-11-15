"""
Rutas del módulo de reportes de AgroCycle.
Genera documentos PDF profesionales para las temporadas agrícolas.
"""
from flask import Blueprint, send_file, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from io import BytesIO

from app.application.use_cases.reportes.generar_ficha_tecnica import GenerarFichaTecnicaUseCase
from app.application.use_cases.reportes.dashboard_temporada import DashboardTemporadaUseCase
from app.application.use_cases.reportes.dashboard_comparativo import DashboardComparativoUseCase
from app.infrastructure.repositories.pg_estimacion_repository import PgEstimacionRepository
from app.infrastructure.repositories.pg_compra_repository import PgCompraRepository
from app.infrastructure.repositories.pg_resultado_financiero_repository import PgResultadoFinancieroRepository
from app.infrastructure.repositories.pg_temporada_parcela_repository import PgTemporadaParcelaRepository
from app.infrastructure.database import get_db
from app.infrastructure.security.decorators import requiere_rol

reportes_bp = Blueprint('reportes', __name__)


@reportes_bp.route(
    '/temporada-parcela/<tp_id>/ficha-tecnica',
    methods=['GET']
)
@jwt_required()
@requiere_rol('agricultor', 'agronomo', 'administrador')
def generar_ficha_tecnica(tp_id):
    """
    CU-REP-001 — Genera y descarga la ficha técnica agrícola en PDF.

    Retorna el PDF directamente como archivo descargable.
    El nombre del archivo incluye el ID de la temporada_parcela
    para facilitar la identificación en el sistema de archivos.
    """
    claims = get_jwt()
    agricultor_id = claims.get('sub')

    db = next(get_db())
    use_case = GenerarFichaTecnicaUseCase(db=db)

    resultado, status = use_case.ejecutar(
        temporada_parcela_id=tp_id,
        agricultor_id=agricultor_id,
    )

    # Si el resultado es un dict es un error
    if isinstance(resultado, dict):
        return jsonify(resultado), status

    # Si es bytes es el PDF — enviarlo como descarga
    nombre_archivo = f"ficha_tecnica_{tp_id[:8]}.pdf"

    return send_file(
        BytesIO(resultado),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=nombre_archivo,
    )


def _repos(db):
    """Instancia el conjunto de repos que comparten los dashboards."""
    return {
        'estimacion_repo': PgEstimacionRepository(db),
        'compra_repo': PgCompraRepository(db),
        'resultado_repo': PgResultadoFinancieroRepository(db),
        'temporada_parcela_repo': PgTemporadaParcelaRepository(db),
    }


@reportes_bp.route('/temporadas/<temporada_id>/dashboard', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def dashboard_temporada(temporada_id):
    """
    CU-REP-004 — Dashboard general de una temporada en JSON.
    Compone financiero + estimación + validación (no genera PDF).
    """
    claims = get_jwt()
    agricultor_id = claims.get('sub')

    db = next(get_db())
    use_case = DashboardTemporadaUseCase(db=db, **_repos(db))

    resultado, status = use_case.ejecutar(
        temporada_id=temporada_id,
        agricultor_id=agricultor_id,
    )
    return jsonify(resultado), status


@reportes_bp.route('/dashboard-comparativo', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def dashboard_comparativo():
    """
    CU-REP-005 — Dashboard comparativo entre todas las temporadas
    del agricultor, en JSON. Compone los indicadores clave de cada una.
    """
    claims = get_jwt()
    agricultor_id = claims.get('sub')

    db = next(get_db())
    use_case = DashboardComparativoUseCase(db=db, **_repos(db))

    resultado, status = use_case.ejecutar(agricultor_id=agricultor_id)
    return jsonify(resultado), status