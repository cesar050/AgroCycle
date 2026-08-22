"""
Rutas HTTP del modulo de Lotes y Parcelas.
Los lotes pertenecen a fincas y las parcelas pertenecen a lotes.
Todos los endpoints requieren JWT valido con rol agricultor.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.application.use_cases.fincas_parcelas.gestionar_lotes import GestionarLotesUseCase
from app.application.use_cases.fincas_parcelas.registrar_parcela import RegistrarParcelaUseCase
from app.infrastructure.repositories.pg_lote_repository import PgLoteRepository
from app.infrastructure.repositories.pg_parcela_repository import PgParcelaRepository
from app.infrastructure.repositories.pg_finca_repository import PgFincaRepository
from app.infrastructure.database import SessionLocal
from app.infrastructure.security.decorators import requiere_rol

lotes_parcelas_bp = Blueprint('lotes_parcelas', __name__)


def get_repos():
    db = SessionLocal()
    return (
        PgLoteRepository(db),
        PgParcelaRepository(db),
        PgFincaRepository(db),
        db
    )


def obtener_agricultor_id() -> str:
    claims = get_jwt()
    perfil_id = claims.get('perfil_id')
    if not perfil_id:
        raise PermissionError("El usuario no tiene perfil de agricultor")
    return perfil_id


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

    lote_repo, parcela_repo, finca_repo, db = get_repos()
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
    lote_repo, parcela_repo, finca_repo, db = get_repos()
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

    lote_repo, parcela_repo, finca_repo, db = get_repos()
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
    Lista todas las parcelas de un lote.
    """
    lote_repo, parcela_repo, finca_repo, db = get_repos()
    try:
        parcelas = parcela_repo.listar_por_lote(lote_id)
        resultado = [
            {
                "id": p.id,
                "lote_id": p.lote_id,
                "nombre": p.nombre,
                "superficie_ha": p.superficie_ha,
                "altitud_promedio_msnm": p.altitud_promedio_msnm,
                "acceso_riego": p.acceso_riego,
                "activo": p.activo
            }
            for p in parcelas
        ]
        return jsonify({"parcelas": resultado, "total": len(resultado)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@lotes_parcelas_bp.route('/parcelas/<parcela_id>/grilla-topografica', methods=['GET'])
@jwt_required()
def ver_grilla_topografica(parcela_id):
    """
    GET /api/v1/parcelas/<uuid>/grilla-topografica
    Retorna el GeoJSON con el poligono y los puntos de la grilla
    para visualizar en geojson.io — solo para desarrollo.
    """
    from app.infrastructure.external.topografia_service import generar_puntos_dentro_poligono
    from geoalchemy2.functions import ST_AsGeoJSON
    from sqlalchemy import text
    import json

    lote_repo, parcela_repo, finca_repo, db = get_repos()
    try:
        parcela = parcela_repo.buscar_por_id(parcela_id)
        if not parcela:
            return jsonify({"error": "Parcela no encontrada"}), 404

        resultado = db.execute(
            text("SELECT ST_AsGeoJSON(geometria) as geojson FROM parcelas WHERE id = :id"),
            {"id": parcela_id}
        ).fetchone()

        poligono_geojson = json.loads(resultado.geojson)
        coordenadas = poligono_geojson['coordinates'][0]

        puntos = generar_puntos_dentro_poligono(
            [[p[0], p[1]] for p in coordenadas],
            parcela.superficie_ha
        )

        features = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": poligono_geojson['coordinates']
                },
                "properties": {
                    "nombre": parcela.nombre,
                    "superficie_ha": parcela.superficie_ha,
                    "tipo": "parcela"
                }
            }
        ]

        for i, (lat, lng) in enumerate(puntos):
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "properties": {
                    "numero": i + 1,
                    "tipo": "punto_grilla"
                }
            })

        return jsonify({
            "type": "FeatureCollection",
            "features": features,
            "total_puntos": len(puntos)
        }), 200

    finally:
        db.close()


@lotes_parcelas_bp.route('/fincas/<finca_id>/parcelas/geojson', methods=['GET'])
@jwt_required()
def parcelas_geojson(finca_id):
    """Retorna todas las parcelas de una finca con su geometría GeoJSON."""
    from sqlalchemy import text
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT
                p.id,
                p.nombre,
                p.superficie_ha,
                p.altitud_promedio_msnm,
                p.pendiente_porcentaje,
                p.orientacion,
                tp.estado_fenologico,
                ST_AsGeoJSON(p.geometria) as geojson
            FROM parcelas p
            JOIN lotes l ON p.lote_id = l.id
            JOIN fincas f ON l.finca_id = f.id
            LEFT JOIN temporada_parcelas tp ON tp.parcela_id = p.id
                AND tp.activo = TRUE
            WHERE f.id = CAST(:finca_id AS uuid)
              AND p.activo = TRUE
            ORDER BY p.nombre
        """), {'finca_id': finca_id}).fetchall()

        parcelas = []
        for r in rows:
            import json
            geojson = json.loads(r.geojson) if r.geojson else None
            parcelas.append({
                'id': str(r.id),
                'nombre': r.nombre,
                'superficie_ha': float(r.superficie_ha or 0),
                'altitud_msnm': float(r.altitud_promedio_msnm or 0),
                'pendiente': float(r.pendiente_porcentaje or 0),
                'orientacion': r.orientacion,
                'estado_fenologico': r.estado_fenologico,
                'geojson': geojson,
            })

        return jsonify({'parcelas': parcelas}), 200
    finally:
        db.close()


@lotes_parcelas_bp.route('/fincas/<finca_id>/mapa', methods=['GET'])
@jwt_required()
def mapa_finca(finca_id):
    """
    Retorna estructura completa: finca → lotes → parcelas
    con geometrías GeoJSON para el mapa SVG.
    """
    import json
    from sqlalchemy import text
    db = SessionLocal()
    try:
        # Finca con su geometría
        finca_row = db.execute(text("""
            SELECT
                f.id, f.nombre, f.superficie_ha,
                f.provincia, f.canton, f.parroquia, f.sector,
                ST_AsGeoJSON(f.geometria) AS geojson_finca
            FROM fincas f
            WHERE f.id = CAST(:finca_id AS uuid)
              AND f.activo = TRUE
        """), {'finca_id': finca_id}).fetchone()

        if not finca_row:
            return jsonify({'error': 'Finca no encontrada'}), 404

        # Lotes con geometría
        lotes_rows = db.execute(text("""
            SELECT
                l.id, l.nombre, l.superficie_ha,
                ST_AsGeoJSON(l.geometria) AS geojson_lote
            FROM lotes l
            WHERE l.finca_id = CAST(:finca_id AS uuid)
              AND l.activo = TRUE
            ORDER BY l.nombre
        """), {'finca_id': finca_id}).fetchall()

        # Parcelas con estado fenológico y estimación
        parcelas_rows = db.execute(text("""
            SELECT
                p.id,
                p.nombre,
                p.superficie_ha,
                p.altitud_promedio_msnm,
                p.pendiente_porcentaje,
                p.orientacion,
                l.id AS lote_id,
                COALESCE(tp.estado_fenologico, 'pre_siembra') AS estado_fenologico,
                COALESCE(tp.avance_ciclo_porcentaje, 0)       AS avance_ciclo,
                COALESCE(tp.produccion_real_qq, 0)            AS produccion_real,
                COALESCE(e.valor_qq_ha, 0)                    AS estimacion_qq_ha,
                ST_AsGeoJSON(p.geometria) AS geojson_parcela
            FROM parcelas p
            JOIN lotes l ON p.lote_id = l.id
            LEFT JOIN temporada_parcelas tp
                ON tp.parcela_id = p.id AND tp.activo = TRUE
            LEFT JOIN LATERAL (
                SELECT ep.valor_qq_ha
                FROM estimaciones_produccion ep
                WHERE ep.temporada_parcela_id = tp.id
                ORDER BY ep.fecha_generacion DESC
                LIMIT 1
            ) e ON TRUE
            WHERE l.finca_id = CAST(:finca_id AS uuid)
              AND p.activo = TRUE
            ORDER BY l.nombre, p.nombre
        """), {'finca_id': finca_id}).fetchall()

        # Agrupar parcelas por lote
        parcelas_por_lote: dict = {}
        for p in parcelas_rows:
            lid = str(p.lote_id)
            if lid not in parcelas_por_lote:
                parcelas_por_lote[lid] = []
            geojson = json.loads(p.geojson_parcela) if p.geojson_parcela else None
            parcelas_por_lote[lid].append({
                'id':               str(p.id),
                'nombre':           p.nombre,
                'superficie_ha':    float(p.superficie_ha or 0),
                'altitud_msnm':     float(p.altitud_promedio_msnm or 0),
                'pendiente':        float(p.pendiente_porcentaje or 0),
                'orientacion':      p.orientacion,
                'estado_fenologico': p.estado_fenologico,
                'avance_ciclo':     float(p.avance_ciclo or 0),
                'produccion_real':  float(p.produccion_real or 0),
                'estimacion_qq_ha': float(p.estimacion_qq_ha or 0),
                'geojson':          geojson,
            })

        # Construir lotes
        lotes = []
        for l in lotes_rows:
            geojson_lote = json.loads(l.geojson_lote) if l.geojson_lote else None
            lotes.append({
                'id':          str(l.id),
                'nombre':      l.nombre,
                'superficie_ha': float(l.superficie_ha or 0),
                'geojson':     geojson_lote,
                'parcelas':    parcelas_por_lote.get(str(l.id), []),
            })

        geojson_finca = json.loads(finca_row.geojson_finca) if finca_row.geojson_finca else None

        return jsonify({
            'finca': {
                'id':           str(finca_row.id),
                'nombre':       finca_row.nombre,
                'superficie_ha': float(finca_row.superficie_ha or 0),
                'provincia':    finca_row.provincia,
                'canton':       finca_row.canton,
                'sector':       finca_row.sector,
                'geojson':      geojson_finca,
                'lotes':        lotes,
            }
        }), 200
    finally:
        db.close()

@lotes_parcelas_bp.route('/fincas/<finca_id>/mapa/topografia', methods=['GET'])
@jwt_required()
def mapa_topografia(finca_id):
    """
    Retorna todos los puntos de la grilla con elevaciones reales
    de NASA SRTM para visualizar el mapa de pendiente de la finca.
    """
    import json
    from sqlalchemy import text
    from app.infrastructure.external.topografia_service import (
        generar_puntos_dentro_poligono, consultar_altitudes
    )
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT
                p.id, p.nombre, p.superficie_ha,
                p.altitud_promedio_msnm,
                p.pendiente_porcentaje,
                ST_AsGeoJSON(p.geometria) AS geojson
            FROM parcelas p
            JOIN lotes l ON p.lote_id = l.id
            WHERE l.finca_id = CAST(:finca_id AS uuid)
              AND p.activo = TRUE
        """), {'finca_id': finca_id}).fetchall()
        resultado = []
        for row in rows:
            if not row.geojson:
                continue
            geojson = json.loads(row.geojson)
            coords  = geojson['coordinates'][0]
            # Generar grilla dentro del polígono
            puntos = generar_puntos_dentro_poligono(
                [[c[0], c[1]] for c in coords],
                float(row.superficie_ha or 0.5)
            )
            if not puntos:
                continue
            # Consultar elevaciones reales
            altitudes = consultar_altitudes(puntos)
            if not altitudes:
                continue
            # Calcular min/max para normalizar colores
            alt_min = min(altitudes)
            alt_max = max(altitudes)
            rango   = alt_max - alt_min or 1
            puntos_con_elev = []
            for i, (lat, lng) in enumerate(puntos):
                if i < len(altitudes):
                    elev = altitudes[i]
                    # Valor normalizado 0-1 para color
                    norm = (elev - alt_min) / rango
                    puntos_con_elev.append({
                        'lat':        lat,
                        'lng':        lng,
                        'elevacion':  elev,
                        'normalizado': round(norm, 3),
                    })
            resultado.append({
                'parcela_id':   str(row.id),
                'nombre':       row.nombre,
                'superficie_ha': float(row.superficie_ha or 0),
                'altitud_min':  alt_min,
                'altitud_max':  alt_max,
                'altitud_prom': float(row.altitud_promedio_msnm or 0),
                'pendiente':    float(row.pendiente_porcentaje or 0),
                'puntos':       puntos_con_elev,
                'geojson':      geojson,
            })
        return jsonify({'parcelas': resultado}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()