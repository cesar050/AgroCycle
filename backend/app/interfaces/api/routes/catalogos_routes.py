"""
Rutas HTTP de catálogos de solo lectura (listas de opciones fijas que
viven en tablas de referencia, no en entidades de negocio).
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.application.use_cases.catalogos.listar_tipos_suelo import ListarTiposSueloUseCase
from app.infrastructure.repositories.pg_tipo_suelo_repository import PgTipoSueloRepository
from app.infrastructure.database import SessionLocal

catalogos_bp = Blueprint('catalogos', __name__)


@catalogos_bp.route('/tipos-suelo', methods=['GET'])
@jwt_required()
def listar_tipos_suelo():
    """GET /api/v1/tipos-suelo — catálogo de tipos de suelo para el formulario de Parcela."""
    db = SessionLocal()
    try:
        use_case = ListarTiposSueloUseCase(PgTipoSueloRepository(db))
        resultado = use_case.ejecutar()
        return jsonify({"tipos_suelo": resultado}), 200
    finally:
        db.close()
