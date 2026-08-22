"""
Rutas HTTP del modulo climatico.
Permite descargar datos climaticos historicos para una parcela
y obtener el pronostico de los proximos dias.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from datetime import date
from sqlalchemy import text
from app.application.use_cases.climatico.descargar_clima import DescargarClimaUseCase
from app.application.use_cases.climatico.calcular_balance_hidrico import CalcularBalanceHidricoUseCase
from app.application.use_cases.climatico.registrar_evento_manual import RegistrarEventoManualUseCase
from app.application.use_cases.climatico.historial_climatico import HistorialClimaticoUseCase
from app.infrastructure.repositories.pg_dato_climatico_repository import PgDatoClimaticoRepository
from app.infrastructure.database import SessionLocal
from app.infrastructure.security.decorators import requiere_rol

climatico_bp = Blueprint('climatico', __name__)


def get_db():
    return SessionLocal()


def obtener_agricultor_id() -> str:
    claims = get_jwt()
    perfil_id = claims.get('perfil_id')
    if not perfil_id:
        raise PermissionError("El usuario no tiene perfil de agricultor")
    return perfil_id


@climatico_bp.route('/parcelas/<parcela_id>/clima', methods=['POST'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def descargar_clima(parcela_id):
    """
    POST /api/v1/climatico/parcelas/<uuid>/clima
    Descarga datos climaticos historicos para una parcela.
    Body: {
        "fecha_inicio": "2026-01-01",
        "fecha_fin": "2026-07-29",
        "temporada_id": "uuid"
    }
    """
    datos = request.get_json()
    if not datos or not datos.get('fecha_inicio') or not datos.get('fecha_fin'):
        return jsonify({"error": "fecha_inicio y fecha_fin son requeridos"}), 400

    db = get_db()
    try:
        resultado_coords = db.execute(
            text("""
                SELECT
                    ST_Y(ST_Centroid(geometria)) as latitud,
                    ST_X(ST_Centroid(geometria)) as longitud
                FROM parcelas
                WHERE id = CAST(:parcela_id AS uuid)
            """),
            {"parcela_id": parcela_id}
        ).fetchone()

        if not resultado_coords or not resultado_coords.latitud:
            return jsonify({"error": "Parcela no encontrada o sin geometria"}), 404

        repo = PgDatoClimaticoRepository(db)
        use_case = DescargarClimaUseCase(repo)
        resultado = use_case.ejecutar(
            parcela_id=parcela_id,
            latitud=resultado_coords.latitud,
            longitud=resultado_coords.longitud,
            fecha_inicio=date.fromisoformat(datos['fecha_inicio']),
            fecha_fin=date.fromisoformat(datos['fecha_fin']),
            temporada_id=datos.get('temporada_id')
        )
        return jsonify(resultado), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@climatico_bp.route('/parcelas/<parcela_id>/clima', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def listar_clima(parcela_id):
    """
    GET /api/v1/climatico/parcelas/<uuid>/clima
    Lista los datos climaticos guardados para una parcela.
    Query params: fecha_inicio, fecha_fin
    """
    fecha_inicio = request.args.get('fecha_inicio', '2026-01-01')
    fecha_fin = request.args.get('fecha_fin', date.today().isoformat())

    db = get_db()
    try:
        repo = PgDatoClimaticoRepository(db)
        datos = repo.listar_por_parcela_y_rango(
            parcela_id,
            date.fromisoformat(fecha_inicio),
            date.fromisoformat(fecha_fin)
        )

        return jsonify({
            "parcela_id": parcela_id,
            "datos": [
                {
                    "fecha": str(d.fecha),
                    "precipitacion_mm": d.precipitacion_mm,
                    "temperatura_max_c": d.temperatura_max_c,
                    "temperatura_min_c": d.temperatura_min_c,
                    "temperatura_promedio_c": d.temperatura_promedio_c,
                    "humedad_relativa_porcentaje": d.humedad_relativa_porcentaje,
                    "radiacion_solar_mj_m2": d.radiacion_solar_mj_m2,
                    "velocidad_viento_km_h": d.velocidad_viento_km_h,
                    "evapotranspiracion_mm": d.evapotranspiracion_mm,
                    "fuente": d.fuente
                }
                for d in datos
            ],
            "total": len(datos)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@climatico_bp.route('/parcelas/<parcela_id>/forecast', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def obtener_forecast(parcela_id):
    """
    GET /api/v1/climatico/parcelas/<uuid>/forecast
    Obtiene el pronostico climatico para los proximos 7 dias.
    """
    db = get_db()
    try:
        resultado = db.execute(
            text("""
                SELECT
                    ST_Y(ST_Centroid(geometria)) as latitud,
                    ST_X(ST_Centroid(geometria)) as longitud
                FROM parcelas
                WHERE id = CAST(:parcela_id AS uuid)
            """),
            {"parcela_id": parcela_id}
        ).fetchone()

        if not resultado or not resultado.latitud:
            return jsonify({"error": "Parcela no encontrada o sin geometria"}), 404

        repo = PgDatoClimaticoRepository(db)
        use_case = DescargarClimaUseCase(repo)
        forecast = use_case.obtener_forecast(
            parcela_id=parcela_id,
            latitud=resultado.latitud,
            longitud=resultado.longitud,
            dias=7
        )

        return jsonify({
            "parcela_id": parcela_id,
            "forecast": forecast,
            "total_dias": len(forecast)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@climatico_bp.route('/temporada-parcelas/<tp_id>/balance-hidrico', methods=['POST'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def calcular_balance_hidrico(tp_id):
    """
    POST /api/v1/climatico/temporada-parcelas/<uuid>/balance-hidrico
    Calcula el balance hidrico FAO-56 para una parcela en una temporada.
    Body: {
        "parcela_id": "uuid",
        "fecha_inicio": "2025-12-01",
        "fecha_fin": "2026-04-30"
    }
    """
    datos = request.get_json()
    if not datos or not datos.get('parcela_id'):
        return jsonify({"error": "parcela_id es requerido"}), 400

    db = get_db()
    try:
        use_case = CalcularBalanceHidricoUseCase(db)
        resultado = use_case.ejecutar(
            temporada_parcela_id=tp_id,
            parcela_id=datos['parcela_id'],
            fecha_inicio=date.fromisoformat(datos.get('fecha_inicio', '2025-12-01')),
            fecha_fin=date.fromisoformat(datos.get('fecha_fin', date.today().isoformat()))
        )
        return jsonify(resultado), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@climatico_bp.route('/alertas', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def generar_alertas():
    """
    GET /api/v1/climatico/alertas
    Genera alertas de humedad para todas las parcelas activas del agricultor.
    """
    db = get_db()
    try:
        from app.application.use_cases.climatico.generar_alertas import GenerarAlertasUseCase
        claims = get_jwt()
        agricultor_id = claims.get('perfil_id')
        use_case = GenerarAlertasUseCase(db)
        resultado = use_case.ejecutar(agricultor_id=agricultor_id)
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@climatico_bp.route('/temporada-parcelas/<tp_id>/estres-hidrico', methods=['POST'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def calcular_estres_hidrico(tp_id):
    """
    POST /api/v1/climatico/temporada-parcelas/<uuid>/estres-hidrico
    Calcula el indice de estres hidrico Ks para un periodo.
    Body: {
        "parcela_id": "uuid",
        "fecha_inicio": "2025-12-15",
        "fecha_fin": "2026-04-30"
    }
    """
    datos = request.get_json()
    if not datos or not datos.get('parcela_id'):
        return jsonify({"error": "parcela_id es requerido"}), 400

    db = get_db()
    try:
        from app.application.use_cases.climatico.calcular_estres_hidrico import CalcularEstresHidricoUseCase
        use_case = CalcularEstresHidricoUseCase(db)
        resultado = use_case.ejecutar(
            temporada_parcela_id=tp_id,
            parcela_id=datos['parcela_id'],
            fecha_inicio=date.fromisoformat(datos.get('fecha_inicio', '2025-12-15')),
            fecha_fin=date.fromisoformat(datos.get('fecha_fin', date.today().isoformat()))
        )
        return jsonify(resultado), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@climatico_bp.route('/parcelas/<parcela_id>/evento-manual', methods=['POST'])
@jwt_required()
@requiere_rol('agricultor', 'administrador')
def registrar_evento_manual(parcela_id):
    """
    CU-CLI-004 — Registra un dato climático manual para una parcela.
    Si ya existe dato para esa fecha lo actualiza.

    Body JSON:
    {
        "fecha": "2026-05-01",
        "precipitacion_mm": 25.5,
        "temperatura_max_c": 28.0,
        "temperatura_min_c": 18.0,
        "humedad_relativa_porcentaje": 75.0
    }
    """
    claims = get_jwt()
    agricultor_id = claims.get('sub')
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Body JSON requerido'}), 400

    if 'fecha' not in data:
        return jsonify({'error': 'Campo requerido: fecha'}), 400

    try:
        fecha = date.fromisoformat(data['fecha'])
    except ValueError:
        return jsonify({
            'error': 'Formato de fecha inválido. Use YYYY-MM-DD'
        }), 400

    db = get_db()
    use_case = RegistrarEventoManualUseCase(db=db)

    resultado, status = use_case.ejecutar(
        parcela_id=parcela_id,
        agricultor_id=agricultor_id,
        fecha=fecha,
        precipitacion_mm=data.get('precipitacion_mm'),
        temperatura_max_c=data.get('temperatura_max_c'),
        temperatura_min_c=data.get('temperatura_min_c'),
        temperatura_promedio_c=data.get('temperatura_promedio_c'),
        humedad_relativa_porcentaje=data.get('humedad_relativa_porcentaje'),
        evapotranspiracion_mm=data.get('evapotranspiracion_mm'),
        velocidad_viento_km_h=data.get('velocidad_viento_km_h'),
    )
    return jsonify(resultado), status


@climatico_bp.route('/parcelas/<parcela_id>/historial', methods=['GET'])
@jwt_required()
@requiere_rol('agricultor', 'agronomo', 'administrador')
def historial_climatico(parcela_id):
    """
    CU-CLI-006 — Historial climático paginado con filtros.

    Query params opcionales:
        fecha_inicio: YYYY-MM-DD
        fecha_fin:    YYYY-MM-DD
        fuente:       api | manual | interpolado
        pagina:       número de página (default 1)
        por_pagina:   registros por página (default 30, máximo 90)
    """
    claims = get_jwt()
    agricultor_id = claims.get('sub')

    fecha_inicio = None
    fecha_fin = None

    try:
        if request.args.get('fecha_inicio'):
            fecha_inicio = date.fromisoformat(
                request.args.get('fecha_inicio')
            )
        if request.args.get('fecha_fin'):
            fecha_fin = date.fromisoformat(
                request.args.get('fecha_fin')
            )
    except ValueError:
        return jsonify({
            'error': 'Formato de fecha inválido. Use YYYY-MM-DD'
        }), 400

    pagina = int(request.args.get('pagina', 1))
    por_pagina = int(request.args.get('por_pagina', 30))
    fuente = request.args.get('fuente')

    db = get_db()
    use_case = HistorialClimaticoUseCase(db=db)

    resultado, status = use_case.ejecutar(
        parcela_id=parcela_id,
        agricultor_id=agricultor_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        fuente=fuente,
        pagina=pagina,
        por_pagina=por_pagina,
    )
    return jsonify(resultado), status