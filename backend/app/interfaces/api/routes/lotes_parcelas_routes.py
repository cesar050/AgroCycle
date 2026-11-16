"""
Rutas HTTP del modulo de Lotes y Parcelas, y de las vistas agregadas
del Mapa (finca completa, topografia, humedad, NDVI). Todo endpoint
aqui invoca un Caso de Uso en application/ — ninguna ruta habla
directo con la base de datos ni con servicios externos.
Todos los endpoints requieren JWT valido con rol agricultor.
"""
from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.application.use_cases.fincas_parcelas.gestionar_lotes import GestionarLotesUseCase
from app.application.use_cases.fincas_parcelas.gestionar_parcelas import GestionarParcelasUseCase
from app.application.use_cases.fincas_parcelas.registrar_parcela import RegistrarParcelaUseCase
from app.application.use_cases.mapa.obtener_mapa_finca import ObtenerMapaFincaUseCase
from app.application.use_cases.mapa.obtener_topografia_finca import ObtenerTopografiaFincaUseCase
from app.application.use_cases.mapa.obtener_parcelas_geojson import ObtenerParcelasGeojsonUseCase
from app.application.use_cases.mapa.obtener_grilla_topografica import ObtenerGrillaTopograficaUseCase
from app.application.use_cases.mapa.obtener_humedad_finca import ObtenerHumedadFincaUseCase
from app.application.use_cases.mapa.obtener_ndvi_finca import ObtenerNdviFincaUseCase
from app.domain.exceptions import ConflictoEliminacionError, ValorInvalidoError
from app.infrastructure.repositories.pg_lote_repository import PgLoteRepository
from app.infrastructure.repositories.pg_parcela_repository import PgParcelaRepository
from app.infrastructure.repositories.pg_finca_repository import PgFincaRepository
from app.infrastructure.repositories.pg_mapa_query_repository import PgMapaQueryRepository
from app.infrastructure.database import SessionLocal
from app.infrastructure.security.decorators import requiere_rol

lotes_parcelas_bp = Blueprint('lotes_parcelas', __name__)


def get_repos():
    db = SessionLocal()
    return (
        PgLoteRepository(db),
        PgParcelaRepository(db),
        PgFincaRepository(db),
        PgMapaQueryRepository(db),
        db
    )


def obtener_agricultor_id() -> str:
    claims = get_jwt()
    perfil_id = claims.get('perfil_id')
    if not perfil_id:
        raise PermissionError("El usuario no tiene perfil de agricultor")
    return perfil_id


# ----------------------------------------------------------------------
# Lotes
# ----------------------------------------------------------------------

@lotes_parcelas_bp.route('/fincas/<finca_id>/lotes', methods=['POST'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def registrar_lote(finca_id):
    """
    POST /api/v1/fincas/<finca_id>/lotes
    Registra un nuevo lote dentro de una finca.
    Body: { "nombre": "Lote Norte", "descripcion": "..." }
    """
    datos = request.get_json()
    if not datos or not datos.get('nombre'):
        return jsonify({"error": "El nombre del lote es requerido"}), 400

    lote_repo, parcela_repo, finca_repo, mapa_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = GestionarLotesUseCase(lote_repo, finca_repo)
        resultado = use_case.registrar(
            finca_id=finca_id,
            agricultor_id=agricultor_id,
            nombre=datos['nombre'],
            coordenadas=datos.get('coordenadas'),
            descripcion=datos.get('descripcion')
        )
        return jsonify(resultado), 201

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    finally:
        db.close()


@lotes_parcelas_bp.route('/fincas/<finca_id>/lotes', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def listar_lotes(finca_id):
    """
    GET /api/v1/fincas/<finca_id>/lotes
    Lista todos los lotes de una finca.
    """
    lote_repo, parcela_repo, finca_repo, mapa_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = GestionarLotesUseCase(lote_repo, finca_repo)
        resultado = use_case.listar(finca_id, agricultor_id)
        return jsonify({"lotes": resultado, "total": len(resultado)}), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    finally:
        db.close()


@lotes_parcelas_bp.route('/lotes/<lote_id>', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def obtener_lote(lote_id):
    """GET /api/v1/lotes/<uuid> — detalle de un lote del agricultor."""
    lote_repo, parcela_repo, finca_repo, mapa_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = GestionarLotesUseCase(lote_repo, finca_repo)
        resultado = use_case.obtener(lote_id, agricultor_id)
        return jsonify(resultado), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    finally:
        db.close()


@lotes_parcelas_bp.route('/lotes/<lote_id>', methods=['PUT'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def editar_lote(lote_id):
    """PUT /api/v1/lotes/<uuid> — edita nombre/descripcion de un lote."""
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "No se recibieron datos"}), 400

    lote_repo, parcela_repo, finca_repo, mapa_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = GestionarLotesUseCase(lote_repo, finca_repo)
        resultado = use_case.editar(lote_id, agricultor_id, datos)
        return jsonify(resultado), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    finally:
        db.close()


@lotes_parcelas_bp.route('/lotes/<lote_id>', methods=['DELETE'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def eliminar_lote(lote_id):
    """
    DELETE /api/v1/lotes/<uuid>
    Elimina (soft-delete) un lote. Responde 409 si tiene parcelas activas.
    """
    lote_repo, parcela_repo, finca_repo, mapa_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = GestionarLotesUseCase(lote_repo, finca_repo)
        resultado = use_case.eliminar(lote_id, agricultor_id)
        return jsonify(resultado), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ConflictoEliminacionError as e:
        return jsonify({"error": str(e)}), 409
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    finally:
        db.close()


# ----------------------------------------------------------------------
# Parcelas
# ----------------------------------------------------------------------

@lotes_parcelas_bp.route('/lotes/<lote_id>/parcelas', methods=['POST'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def registrar_parcela(lote_id):
    """
    POST /api/v1/lotes/<lote_id>/parcelas
    Registra una nueva parcela con geometria real.
    Body: {
        "nombre": "Parcela 1",
        "coordenadas": [[-79.845, -4.123], [-79.844, -4.123],
                        [-79.844, -4.124], [-79.845, -4.124]],
        "tipo_suelo_id": 1,
        "drenaje": "moderado",
        "acceso_riego": false
    }
    """
    datos = request.get_json()
    if not datos or not datos.get('nombre'):
        return jsonify({"error": "El nombre de la parcela es requerido"}), 400

    if not datos.get('coordenadas') or len(datos['coordenadas']) < 3:
        return jsonify({"error": "Se requieren al menos 3 coordenadas para definir el poligono"}), 400

    lote_repo, parcela_repo, finca_repo, mapa_repo, db = get_repos()
    try:
        use_case = RegistrarParcelaUseCase(parcela_repo, lote_repo)
        resultado = use_case.ejecutar(
            lote_id=lote_id,
            nombre=datos['nombre'],
            coordenadas=datos['coordenadas'],
            tipo_suelo_id=datos.get('tipo_suelo_id'),
            drenaje=datos.get('drenaje'),
            acceso_riego=datos.get('acceso_riego', False),
            tipo_riego=datos.get('tipo_riego'),
            observaciones=datos.get('observaciones')
        )
        return jsonify(resultado), 201

    except ValorInvalidoError as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@lotes_parcelas_bp.route('/lotes/<lote_id>/parcelas', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def listar_parcelas(lote_id):
    """
    GET /api/v1/lotes/<lote_id>/parcelas
    Lista todas las parcelas activas de un lote del agricultor.
    """
    lote_repo, parcela_repo, finca_repo, mapa_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = GestionarParcelasUseCase(parcela_repo, lote_repo, finca_repo)
        resultado = use_case.listar(lote_id, agricultor_id)
        return jsonify({"parcelas": resultado, "total": len(resultado)}), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    finally:
        db.close()


@lotes_parcelas_bp.route('/parcelas/<parcela_id>', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def obtener_parcela(parcela_id):
    """GET /api/v1/parcelas/<uuid> — detalle completo de una parcela."""
    lote_repo, parcela_repo, finca_repo, mapa_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = GestionarParcelasUseCase(parcela_repo, lote_repo, finca_repo)
        resultado = use_case.obtener(parcela_id, agricultor_id)
        return jsonify(resultado), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    finally:
        db.close()


@lotes_parcelas_bp.route('/parcelas/<parcela_id>', methods=['PUT'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def editar_parcela(parcela_id):
    """PUT /api/v1/parcelas/<uuid> — edita atributos agronomicos de una parcela."""
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "No se recibieron datos"}), 400

    lote_repo, parcela_repo, finca_repo, mapa_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = GestionarParcelasUseCase(parcela_repo, lote_repo, finca_repo)
        resultado = use_case.editar(parcela_id, agricultor_id, datos)
        return jsonify(resultado), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValorInvalidoError as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    finally:
        db.close()


@lotes_parcelas_bp.route('/parcelas/<parcela_id>', methods=['DELETE'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def eliminar_parcela(parcela_id):
    """
    DELETE /api/v1/parcelas/<uuid>
    Elimina (soft-delete) una parcela. Nunca responde 409: la parcela
    es una hoja del arbol finca->lote->parcela.
    """
    lote_repo, parcela_repo, finca_repo, mapa_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = GestionarParcelasUseCase(parcela_repo, lote_repo, finca_repo)
        resultado = use_case.eliminar(parcela_id, agricultor_id)
        return jsonify(resultado), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    finally:
        db.close()


@lotes_parcelas_bp.route('/parcelas/<parcela_id>/grilla-topografica', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def ver_grilla_topografica(parcela_id):
    """
    GET /api/v1/parcelas/<uuid>/grilla-topografica
    Retorna el GeoJSON con el poligono y los puntos de la grilla
    para visualizar en geojson.io — solo para desarrollo.
    """
    lote_repo, parcela_repo, finca_repo, mapa_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = ObtenerGrillaTopograficaUseCase(parcela_repo, lote_repo, finca_repo, mapa_repo)
        resultado = use_case.ejecutar(parcela_id, agricultor_id)
        return jsonify(resultado), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    finally:
        db.close()


# ----------------------------------------------------------------------
# Vistas agregadas del Mapa
# ----------------------------------------------------------------------

@lotes_parcelas_bp.route('/fincas/<finca_id>/parcelas/geojson', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def parcelas_geojson(finca_id):
    """Retorna todas las parcelas de una finca con su geometría GeoJSON."""
    lote_repo, parcela_repo, finca_repo, mapa_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = ObtenerParcelasGeojsonUseCase(finca_repo, mapa_repo)
        resultado = use_case.ejecutar(finca_id, agricultor_id)
        return jsonify({'parcelas': resultado}), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    finally:
        db.close()


@lotes_parcelas_bp.route('/fincas/<finca_id>/mapa', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def mapa_finca(finca_id):
    """
    Retorna estructura completa: finca → lotes → parcelas
    con geometrías GeoJSON para el visor de Mapa General.
    """
    lote_repo, parcela_repo, finca_repo, mapa_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = ObtenerMapaFincaUseCase(finca_repo, mapa_repo)
        resultado = use_case.ejecutar(finca_id, agricultor_id)
        return jsonify(resultado), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    finally:
        db.close()


@lotes_parcelas_bp.route('/fincas/<finca_id>/mapa/topografia', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def mapa_topografia(finca_id):
    """
    Retorna todos los puntos de la grilla con elevaciones reales
    de NASA SRTM para visualizar el mapa de pendiente de la finca.
    """
    lote_repo, parcela_repo, finca_repo, mapa_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = ObtenerTopografiaFincaUseCase(finca_repo, mapa_repo)
        resultado = use_case.ejecutar(finca_id, agricultor_id)
        return jsonify({'parcelas': resultado}), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@lotes_parcelas_bp.route('/fincas/<finca_id>/mapa/humedad', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def mapa_humedad(finca_id):
    """
    Retorna, por cada parcela de la finca, la humedad de suelo actual
    (Open-Meteo) y el coeficiente de estres hidrico bidireccional
    Ks_final = min(Ks_deficit, Ks_exceso) para el mapa de humedad.
    """
    lote_repo, parcela_repo, finca_repo, mapa_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = ObtenerHumedadFincaUseCase(finca_repo, mapa_repo)
        resultado = use_case.ejecutar(finca_id, agricultor_id)
        return jsonify({'parcelas': resultado}), 200

    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@lotes_parcelas_bp.route('/fincas/<finca_id>/mapa/ndvi', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def mapa_ndvi(finca_id):
    """
    Retorna una imagen PNG con el indice NDVI (Sentinel-2 L2A) de
    Copernicus Data Space Ecosystem recortada al area de la finca.
    Query params: fecha=YYYY-MM-DD (opcional, default hoy - 10 dias,
    para dar margen a la revisita de Sentinel-2 de ~5 dias).
    """
    lote_repo, parcela_repo, finca_repo, mapa_repo, db = get_repos()
    try:
        agricultor_id = obtener_agricultor_id()
        use_case = ObtenerNdviFincaUseCase(finca_repo, mapa_repo)
        imagen = use_case.ejecutar(finca_id, agricultor_id, request.args.get('fecha'))

        if not imagen:
            return jsonify({'error': 'ndvi_no_disponible'}), 503

        return Response(imagen, mimetype='image/png')

    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()
