"""
Rutas HTTP del modulo de Temporadas.
Todos los endpoints requieren JWT valido con rol agricultor.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from datetime import date
from app.application.use_cases.temporadas.registrar_temporada import RegistrarTemporadaUseCase
from app.application.use_cases.temporadas.gestionar_temporada import GestionarTemporadaUseCase
from app.application.use_cases.temporadas.historial_temporadas import HistorialTemporadasUseCase
from app.infrastructure.repositories.pg_temporada_repository import PgTemporadaRepository
from app.infrastructure.repositories.pg_temporada_parcela_repository import PgTemporadaParcelaRepository
from app.infrastructure.repositories.pg_finca_repository import PgFincaRepository
from app.infrastructure.repositories.pg_parcela_repository import PgParcelaRepository
from app.infrastructure.database import SessionLocal
from app.infrastructure.security.decorators import requiere_rol
from app.infrastructure.database import get_db

temporadas_bp = Blueprint('temporadas', __name__)


def get_repos():
    db = SessionLocal()
    return (
        PgTemporadaRepository(db),
        PgTemporadaParcelaRepository(db),
        PgFincaRepository(db),
        PgParcelaRepository(db),
        db
    )


def obtener_agricultor_id() -> str:
    claims = get_jwt()
    perfil_id = claims.get('perfil_id')
    if not perfil_id:
        raise PermissionError("El usuario no tiene perfil de agricultor")
    return perfil_id


@temporadas_bp.route('', methods=['POST'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def registrar_temporada():
    """
    POST /api/v1/temporadas
    Registra una nueva temporada de siembra.
    Body: {
        "finca_id": "uuid",
        "cultivo_id": 1,
        "nombre": "Temporada 2026-2027",
        "fecha_inicio": "2026-12-01",
        "fecha_fin_estimada": "2027-04-30",
        "observaciones": "..."
    }
    """
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "No se recibieron datos"}), 400

    campos_requeridos = ['finca_id', 'cultivo_id', 'nombre', 'fecha_inicio']
    for campo in campos_requeridos:
        if not datos.get(campo):
            return jsonify({"error": f"El campo '{campo}' es requerido"}), 400

    temporada_repo, tp_repo, finca_repo, parcela_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = RegistrarTemporadaUseCase(temporada_repo, finca_repo)
        resultado = use_case.ejecutar(
            agricultor_id=agricultor_id,
            finca_id=datos['finca_id'],
            cultivo_id=datos['cultivo_id'],
            nombre=datos['nombre'],
            fecha_inicio=date.fromisoformat(datos['fecha_inicio']),
            fecha_fin_estimada=date.fromisoformat(datos['fecha_fin_estimada']) if datos.get('fecha_fin_estimada') else None,
            observaciones=datos.get('observaciones')
        )
        return jsonify(resultado), 201

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    finally:
        db.close()


@temporadas_bp.route('', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def listar_temporadas():
    """GET /api/v1/temporadas — Lista todas las temporadas del agricultor."""
    temporada_repo, tp_repo, finca_repo, parcela_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = GestionarTemporadaUseCase(temporada_repo, tp_repo, parcela_repo)
        resultado = use_case.listar(agricultor_id)
        return jsonify({"temporadas": resultado, "total": len(resultado)}), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@temporadas_bp.route('/<temporada_id>', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def obtener_temporada(temporada_id):
    """GET /api/v1/temporadas/<uuid> — Detalle de una temporada con sus parcelas."""
    temporada_repo, tp_repo, finca_repo, parcela_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = GestionarTemporadaUseCase(temporada_repo, tp_repo, parcela_repo)
        resultado = use_case.obtener(temporada_id, agricultor_id)
        return jsonify(resultado), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    finally:
        db.close()


@temporadas_bp.route('/<temporada_id>/parcelas', methods=['POST'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def vincular_parcela(temporada_id):
    """
    POST /api/v1/temporadas/<uuid>/parcelas
    Vincula una parcela a la temporada para sembrar en ella.
    Body: {
        "parcela_id": "uuid",
        "variedad_semilla_id": 1,
        "fecha_siembra": "2026-12-15",
        "densidad_siembra_kg_ha": 25.0,
        "cantidad_semilla_kg": 16.9
    }
    """
    datos = request.get_json()
    if not datos or not datos.get('parcela_id'):
        return jsonify({"error": "El campo parcela_id es requerido"}), 400

    temporada_repo, tp_repo, finca_repo, parcela_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = GestionarTemporadaUseCase(temporada_repo, tp_repo, parcela_repo)
        resultado = use_case.vincular_parcela(
            temporada_id=temporada_id,
            agricultor_id=agricultor_id,
            parcela_id=datos['parcela_id'],
            variedad_semilla_id=datos.get('variedad_semilla_id'),
            fecha_siembra=date.fromisoformat(datos['fecha_siembra']) if datos.get('fecha_siembra') else None,
            densidad_siembra_kg_ha=datos.get('densidad_siembra_kg_ha'),
            cantidad_semilla_kg=datos.get('cantidad_semilla_kg')
        )
        return jsonify(resultado), 201

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    finally:
        db.close()


@temporadas_bp.route('/<temporada_id>/cerrar', methods=['PATCH'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def cerrar_temporada(temporada_id):
    """
    PATCH /api/v1/temporadas/<uuid>/cerrar
    Cierra una temporada activa.
    Body: { "fecha_fin_real": "2027-04-30", "observaciones": "..." }
    """
    datos = request.get_json()
    if not datos or not datos.get('fecha_fin_real'):
        return jsonify({"error": "El campo fecha_fin_real es requerido"}), 400

    temporada_repo, tp_repo, finca_repo, parcela_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = GestionarTemporadaUseCase(temporada_repo, tp_repo, parcela_repo)
        resultado = use_case.cerrar(
            temporada_id=temporada_id,
            agricultor_id=agricultor_id,
            fecha_fin_real=date.fromisoformat(datos['fecha_fin_real']),
            observaciones=datos.get('observaciones')
        )
        return jsonify(resultado), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    finally:
        db.close()

@temporadas_bp.route('/<temporada_id>/fenologia', methods=['PATCH'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def actualizar_fenologia(temporada_id):
    """
    PATCH /api/v1/temporadas/<uuid>/fenologia
    Actualiza el estado fenologico de todas las parcelas de la temporada.
    """
    db = SessionLocal()
    try:
        from app.application.use_cases.temporadas.actualizar_fenologia import ActualizarFenologiaUseCase
        from app.infrastructure.repositories.pg_temporada_parcela_repository import PgTemporadaParcelaRepository
        tp_repo = PgTemporadaParcelaRepository(db)
        use_case = ActualizarFenologiaUseCase(tp_repo, db)
        resultado = use_case.ejecutar(temporada_id=temporada_id)
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@temporadas_bp.route('/<temporada_id>/parcelas/<tp_id>/cosecha', methods=['POST'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def registrar_cosecha(temporada_id, tp_id):
    """
    POST /api/v1/temporadas/<uuid>/parcelas/<uuid>/cosecha
    Registra la produccion real cosechada en una parcela.
    Body: {
        "produccion_real_qq": 85.5,
        "fecha_cosecha": "2027-04-15",
        "precio_venta_qq": 18.50,
        "volumen_vendido_qq": 70.0,
        "produccion_autoconsumo_qq": 15.5
    }
    """
    datos = request.get_json()
    if not datos or not datos.get('produccion_real_qq') or not datos.get('fecha_cosecha'):
        return jsonify({"error": "produccion_real_qq y fecha_cosecha son requeridos"}), 400

    db = SessionLocal()
    try:
        from app.application.use_cases.temporadas.registrar_cosecha import RegistrarCosechaUseCase
        from app.infrastructure.repositories.pg_temporada_parcela_repository import PgTemporadaParcelaRepository
        from app.infrastructure.repositories.pg_temporada_repository import PgTemporadaRepository
        agricultor_id = obtener_agricultor_id()
        tp_repo = PgTemporadaParcelaRepository(db)
        temporada_repo = PgTemporadaRepository(db)
        use_case = RegistrarCosechaUseCase(tp_repo, temporada_repo)
        resultado = use_case.ejecutar(
            temporada_parcela_id=tp_id,
            agricultor_id=agricultor_id,
            produccion_real_qq=float(datos['produccion_real_qq']),
            fecha_cosecha=date.fromisoformat(datos['fecha_cosecha']),
            precio_venta_qq=datos.get('precio_venta_qq'),
            volumen_vendido_qq=datos.get('volumen_vendido_qq'),
            produccion_autoconsumo_qq=datos.get('produccion_autoconsumo_qq'),
            observaciones=datos.get('observaciones')
        )
        return jsonify(resultado), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@temporadas_bp.route('/<temporada_id>/cancelar', methods=['PATCH'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def cancelar_temporada(temporada_id):
    """
    PATCH /api/v1/temporadas/<uuid>/cancelar
    Cancela una temporada activa.
    Body: { "motivo": "Sequia severa" }
    """
    datos = request.get_json()
    db = SessionLocal()
    try:
        agricultor_id = obtener_agricultor_id()
        temporada_repo, tp_repo, finca_repo, parcela_repo, db2 = get_repos()
        use_case = GestionarTemporadaUseCase(temporada_repo, tp_repo, parcela_repo)

        temporada = temporada_repo.buscar_por_id(temporada_id)
        if not temporada:
            return jsonify({"error": "Temporada no encontrada"}), 404
        if not temporada.es_del_agricultor(agricultor_id):
            return jsonify({"error": "No tienes permiso"}), 403
        if temporada.estado != 'activa':
            return jsonify({"error": f"La temporada ya esta {temporada.estado}"}), 409

        temporada.estado = 'cancelada'
        if datos and datos.get('motivo'):
            temporada.observaciones = datos['motivo']
        temporada_repo.actualizar(temporada)

        return jsonify({
            "id": temporada.id,
            "estado": "cancelada",
            "mensaje": "Temporada cancelada exitosamente"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@temporadas_bp.route('/historial', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def historial_temporadas():
    """
    CU-TEM-006 — Historial completo de temporadas del agricultor
    con resumen de producción, financiero y comparativos.
    """
    claims = get_jwt()
    agricultor_id = claims.get('sub')

    db = next(get_db())
    use_case = HistorialTemporadasUseCase(db=db)
    resultado, status = use_case.ejecutar(agricultor_id=agricultor_id)
    return jsonify(resultado), status