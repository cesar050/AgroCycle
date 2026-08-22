"""
Rutas del módulo financiero de AgroCycle.
Gestiona compras, gastos y rentabilidad de temporadas agrícolas.
"""
from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from app.application.use_cases.financiero.registrar_compra import RegistrarCompraUseCase
from app.application.use_cases.financiero.listar_gastos import ListarGastosUseCase
from app.application.use_cases.financiero.calcular_rentabilidad import CalcularRentabilidadUseCase
from app.application.use_cases.financiero.eliminar_compra import EliminarCompraUseCase
from app.application.use_cases.financiero.registrar_venta import RegistrarVentaUseCase
from app.infrastructure.repositories.pg_compra_repository import PgCompraRepository
from app.infrastructure.repositories.pg_resultado_financiero_repository import PgResultadoFinancieroRepository
from app.infrastructure.database import get_db
from app.infrastructure.security.decorators import requiere_rol

financiero_bp = Blueprint('financiero', __name__)


@financiero_bp.route('/temporadas/<temporada_id>/compras', methods=['POST'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def registrar_compra(temporada_id):
    """
    CU-FIN-001 — Registra una compra o gasto en la temporada.

    Body JSON esperado:
    {
        "categoria": "fertilizantes",
        "cantidad": 2,
        "precio_unitario": 45.50,
        "fecha_compra": "2026-01-15",
        "producto_personalizado": "Urea 46%",
        "unidad_medida": "sacos",
        "proveedor": "Agroquímicos Loja",
        "insumo_id": null,
        "actividad_id": null
    }
    """
    claims = get_jwt()
    agricultor_id = claims.get('sub')
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Body JSON requerido'}), 400

    # Validar campos obligatorios
    campos_requeridos = ['categoria', 'cantidad', 'precio_unitario', 'fecha_compra']
    for campo in campos_requeridos:
        if campo not in data:
            return jsonify({
                'error': f"Campo requerido faltante: {campo}"
            }), 400

    # Parsear fecha
    try:
        fecha_compra = date.fromisoformat(data['fecha_compra'])
    except ValueError:
        return jsonify({
            'error': 'Formato de fecha inválido. Use YYYY-MM-DD'
        }), 400

    db = next(get_db())
    use_case = RegistrarCompraUseCase(
        db=db,
        compra_repo=PgCompraRepository(db),
    )

    resultado, status = use_case.ejecutar(
        temporada_id=temporada_id,
        agricultor_id=agricultor_id,
        categoria=data['categoria'],
        cantidad=float(data['cantidad']),
        precio_unitario=float(data['precio_unitario']),
        fecha_compra=fecha_compra,
        insumo_id=data.get('insumo_id'),
        producto_personalizado=data.get('producto_personalizado'),
        unidad_medida=data.get('unidad_medida'),
        proveedor=data.get('proveedor'),
        actividad_id=data.get('actividad_id'),
        usuario_id=agricultor_id,
    )
    return jsonify(resultado), status


@financiero_bp.route('/temporadas/<temporada_id>/gastos', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def listar_gastos(temporada_id):
    """
    CU-FIN-003 — Lista todos los gastos de la temporada con resumen.

    Query params opcionales:
        categoria: filtra por categoría específica
    """
    claims = get_jwt()
    agricultor_id = claims.get('sub')
    categoria = request.args.get('categoria')

    db = next(get_db())
    use_case = ListarGastosUseCase(
        db=db,
        compra_repo=PgCompraRepository(db),
    )

    resultado, status = use_case.ejecutar(
        temporada_id=temporada_id,
        agricultor_id=agricultor_id,
        categoria=categoria,
    )
    return jsonify(resultado), status


@financiero_bp.route('/temporadas/<temporada_id>/rentabilidad', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def calcular_rentabilidad(temporada_id):
    """
    CU-FIN-004 — Calcula y retorna la rentabilidad de la temporada.

    Puede llamarse en cualquier momento — si la temporada está
    activa muestra la situación financiera parcial. Si está
    cerrada muestra el resultado final con costo por quintal.
    """
    claims = get_jwt()
    agricultor_id = claims.get('sub')

    db = next(get_db())
    use_case = CalcularRentabilidadUseCase(
        db=db,
        compra_repo=PgCompraRepository(db),
        resultado_repo=PgResultadoFinancieroRepository(db),
    )

    resultado, status = use_case.ejecutar(
        temporada_id=temporada_id,
        agricultor_id=agricultor_id,
    )
    return jsonify(resultado), status


@financiero_bp.route('/compras/<compra_id>', methods=['DELETE'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def eliminar_compra(compra_id):
    """
    CU-FIN — Elimina una compra registrada por error.
    Solo disponible mientras la temporada esté activa.
    """
    claims = get_jwt()
    agricultor_id = claims.get('sub')

    db = next(get_db())
    use_case = EliminarCompraUseCase(
        db=db,
        compra_repo=PgCompraRepository(db),
    )

    resultado, status = use_case.ejecutar(
        compra_id=compra_id,
        agricultor_id=agricultor_id,
    )
    return jsonify(resultado), status


@financiero_bp.route(
    '/temporada-parcela/<tp_id>/venta',
    methods=['POST']
)
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def registrar_venta(tp_id):
    """
    CU-FIN-002 — Registra la venta de cosecha de una parcela.

    Body JSON:
    {
        "produccion_real_qq": 48.5,
        "fecha_cosecha": "2026-04-20",
        "precio_venta_qq": 32.50,
        "volumen_vendido_qq": 40.0,
        "produccion_autoconsumo_qq": 8.5
    }
    """
    claims = get_jwt()
    agricultor_id = claims.get('sub')
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Body JSON requerido'}), 400

    campos_requeridos = [
        'produccion_real_qq', 'fecha_cosecha',
        'precio_venta_qq', 'volumen_vendido_qq'
    ]
    for campo in campos_requeridos:
        if campo not in data:
            return jsonify({
                'error': f'Campo requerido faltante: {campo}'
            }), 400

    try:
        fecha_cosecha = date.fromisoformat(data['fecha_cosecha'])
    except ValueError:
        return jsonify({
            'error': 'Formato de fecha inválido. Use YYYY-MM-DD'
        }), 400

    db = next(get_db())
    use_case = RegistrarVentaUseCase(db=db)

    resultado, status = use_case.ejecutar(
        temporada_parcela_id=tp_id,
        agricultor_id=agricultor_id,
        produccion_real_qq=float(data['produccion_real_qq']),
        fecha_cosecha=fecha_cosecha,
        precio_venta_qq=float(data['precio_venta_qq']),
        volumen_vendido_qq=float(data['volumen_vendido_qq']),
        produccion_autoconsumo_qq=data.get('produccion_autoconsumo_qq'),
    )
    return jsonify(resultado), status