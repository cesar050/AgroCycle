"""
Rutas del módulo de reportes de AgroCycle.
Genera documentos PDF profesionales para las temporadas agrícolas.
"""
from flask import Blueprint, send_file, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from io import BytesIO

from app.application.use_cases.reportes.generar_ficha_tecnica import GenerarFichaTecnicaUseCase
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