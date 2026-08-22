"""
Rutas HTTP del módulo de autenticación.
Solo maneja HTTP: recibe requests, llama casos de uso y retorna responses.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from app.application.use_cases.administracion.autenticar_usuario import AutenticarUsuarioUseCase
from app.application.use_cases.administracion.registrar_usuario import RegistrarUsuarioUseCase
from app.infrastructure.repositories.pg_usuario_repository import PgUsuarioRepository
from app.infrastructure.repositories.pg_agricultor_repository import PgAgricultorRepository
from app.infrastructure.repositories.pg_agronomo_repository import PgAgronomoRepository
from app.infrastructure.external.email_service import (
    generar_token_verificacion,
    verificar_token,
    enviar_correo_verificacion
)
from app.interfaces.api.schemas.auth_schema import validar_datos_registro
from app.infrastructure.database import SessionLocal
from app.infrastructure.security.rate_limiter import limiter
from app.application.use_cases.administracion.activar_2fa import ActivarDosFactoresUseCase
from app.application.use_cases.administracion.verificar_totp_login import VerificarTOTPLoginUseCase
from app.application.use_cases.administracion.recuperar_password import RecuperarPasswordUseCase
from app.application.use_cases.administracion.resetear_password import ResetearPasswordUseCase
import os
from app.infrastructure.database import get_db
from sqlalchemy import text
import threading

auth_bp = Blueprint('auth', __name__)


def get_repo():
    """
    Fabrica que crea los repositorios con sesión compartida.
    Los tres repositorios comparten la misma sesión de BD
    para garantizar consistencia transaccional.
    """
    db = SessionLocal()
    usuario_repo = PgUsuarioRepository(db)
    agricultor_repo = PgAgricultorRepository(db)
    agronomo_repo = PgAgronomoRepository(db)
    return usuario_repo, agricultor_repo, agronomo_repo, db


def enviar_correo_en_background(app, correo, nombre, token):
    """
    Envía el correo de verificación en un hilo separado.
    Evita que el registro se bloquee esperando al servidor SMTP.
    """
    with app.app_context():
        enviar_correo_verificacion(correo, nombre, token)


@auth_bp.route('/registro', methods=['POST'])
@limiter.limit('3 per hour')
def registro():
    """
    POST /api/v1/auth/registro
    Registra nuevo usuario. Por defecto crea agricultor (rol_id=2).
    Para agrónomo enviar rol_id=3 con numero_registro obligatorio.

    Body para agricultor:
    {
        "nombre": "Juan",
        "apellido": "Pérez",
        "correo": "juan@email.com",
        "password": "Password123!",
        "rol_id": 2
    }

    Body para agrónomo:
    {
        "nombre": "Carlos",
        "apellido": "López",
        "correo": "carlos@email.com",
        "password": "Password123!",
        "rol_id": 3,
        "numero_registro": "ING-AGR-001",
        "especialidad": "Cultivos tropicales"
    }
    """
    datos = request.get_json()
    if not datos:
        return jsonify({'error': 'No se recibieron datos'}), 400

    valido, errores = validar_datos_registro(datos)
    if not valido:
        return jsonify({'error': 'Datos inválidos', 'detalles': errores}), 422

    usuario_repo, agricultor_repo, agronomo_repo, db = get_repo()
    try:
        use_case = RegistrarUsuarioUseCase(
            usuario_repository=usuario_repo,
            agricultor_repository=agricultor_repo,
            agronomo_repository=agronomo_repo,
        )
        resultado = use_case.ejecutar(
            nombre=datos['nombre'],
            apellido=datos['apellido'],
            correo=datos['correo'],
            password=datos['password'],
            rol_id=datos.get('rol_id', 2),
            numero_registro=datos.get('numero_registro'),
            especialidad=datos.get('especialidad'),
        )

        token = generar_token_verificacion(datos['correo'])
        usuario = usuario_repo.buscar_por_correo(datos['correo'])
        usuario.token_verificacion = token
        usuario_repo.actualizar(usuario)

        app = current_app._get_current_object()
        hilo = threading.Thread(
            target=enviar_correo_en_background,
            args=(app, datos['correo'], datos['nombre'], token)
        )
        hilo.daemon = True
        hilo.start()

        respuesta = {
            'mensaje': 'Usuario registrado exitosamente. Revisa tu correo para verificar tu cuenta.',
            'usuario': resultado
        }

        if current_app.config.get('FLASK_ENV') == 'development':
            respuesta['dev_verificacion_url'] = (
                f"http://localhost:5000/api/v1/auth/verificar/{token}"
            )

        return jsonify(respuesta), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 409
    finally:
        db.close()


@auth_bp.route('/verificar/<token>', methods=['GET'])
@limiter.limit('10 per hour')
def verificar_correo(token):
    """
    GET /api/v1/auth/verificar/<token>
    Verifica el correo usando el token del enlace enviado.
    """
    correo = verificar_token(token)
    if not correo:
        return jsonify({
            'error': 'El enlace de verificación es inválido o expiró. Solicita uno nuevo.'
        }), 400

    usuario_repo, agricultor_repo, agronomo_repo, db = get_repo()
    try:
        usuario = usuario_repo.buscar_por_correo(correo)
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404

        if usuario.correo_verificado:
            return jsonify({
                'mensaje': 'Tu correo ya fue verificado anteriormente'
            }), 200

        usuario.correo_verificado = True
        usuario.token_verificacion = None
        usuario_repo.actualizar(usuario)

        return jsonify({
            'mensaje': 'Correo verificado exitosamente. Ya puedes iniciar sesión en AgroCycle.'
        }), 200

    finally:
        db.close()


@auth_bp.route('/login', methods=['POST'])
@limiter.limit('5 per minute')
def login():
    """
    POST /api/v1/auth/login

    Si el usuario tiene 2FA activo retorna un token temporal
    con claims especiales. El cliente debe hacer un segundo
    request a /2fa/verificar-login con el código TOTP.

    Si no tiene 2FA retorna el JWT completo directamente.
    """
    datos = request.get_json()
    if not datos or not datos.get('correo') or not datos.get('password'):
        return jsonify({'error': 'Correo y contraseña son requeridos'}), 400

    usuario_repo, agricultor_repo, agronomo_repo, db = get_repo()
    try:
        use_case = AutenticarUsuarioUseCase(usuario_repo)
        resultado = use_case.ejecutar(
            correo=datos['correo'],
            password=datos['password']
        )

        # Buscar perfil_id según rol
        perfil_id = None
        rol_id = resultado['rol_id']

        if rol_id == 2:
            perfil = agricultor_repo.buscar_por_usuario_id(resultado['id'])
            perfil_id = str(perfil.id) if perfil else None
        elif rol_id == 3:
            perfil = agronomo_repo.buscar_por_usuario_id(resultado['id'])
            perfil_id = str(perfil.id) if perfil else None

        additional_claims = {
            'rol': rol_id,
            'perfil_id': perfil_id,
        }

        # Verificar si tiene 2FA activo
        row = db.execute(
            text("""
                SELECT totp_activo FROM usuarios
                WHERE id = CAST(:usuario_id AS uuid)
            """),
            {'usuario_id': resultado['id']}
        ).fetchone()

        tiene_2fa = row and row.totp_activo

        if tiene_2fa:
            # Emitir token temporal — solo dura 5 minutos
            # El cliente debe completar el login con el código TOTP
            from datetime import timedelta
            token_temporal = create_access_token(
                identity=resultado['id'],
                additional_claims={**additional_claims, 'totp_pendiente': True},
                expires_delta=timedelta(minutes=5),
            )
            return jsonify({
                'requiere_2fa': True,
                'token_temporal': token_temporal,
                'mensaje': 'Ingresa el código de 6 dígitos de tu app autenticadora.',
            }), 200

        # Sin 2FA — login completo directo
        access_token = create_access_token(
            identity=resultado['id'],
            additional_claims=additional_claims,
        )
        refresh_token = create_refresh_token(
            identity=resultado['id'],
            additional_claims=additional_claims,
        )

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'usuario': resultado,
            'requiere_2fa': False,
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    finally:
        db.close()

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """POST /api/v1/auth/refresh — Renueva el access token."""
    usuario_id = get_jwt_identity()
    nuevo_token = create_access_token(identity=usuario_id)
    return jsonify({'access_token': nuevo_token}), 200


@auth_bp.route('/ping', methods=['GET'])
def ping():
    return jsonify({'mensaje': 'Módulo de autenticación activo'}), 200

# ----------------------------------------------------------------
# 2FA — Autenticación de dos factores
# ----------------------------------------------------------------

@auth_bp.route('/2fa/generar-qr', methods=['POST'])
@jwt_required()
def generar_qr_2fa():
    """
    Paso 1 de activación del 2FA.
    Genera el secreto y retorna el QR para escanear.
    El usuario debe estar autenticado con su contraseña normal.
    """
    claims = get_jwt()
    usuario_id = claims.get('sub')
    db = next(get_db())

    use_case = ActivarDosFactoresUseCase(db=db)
    resultado, status = use_case.generar_qr(usuario_id=usuario_id)
    return jsonify(resultado), status


@auth_bp.route('/2fa/confirmar', methods=['POST'])
@jwt_required()
def confirmar_2fa():
    """
    Paso 2 de activación del 2FA.
    Verifica el código de la app y activa el 2FA definitivamente.

    Body JSON:
    {
        "codigo": "123456"
    }
    """
    claims = get_jwt()
    usuario_id = claims.get('sub')
    data = request.get_json()

    if not data or not data.get('codigo'):
        return jsonify({'error': 'Campo requerido: codigo'}), 400

    db = next(get_db())
    use_case = ActivarDosFactoresUseCase(db=db)
    resultado, status = use_case.confirmar_activacion(
        usuario_id=usuario_id,
        codigo=str(data['codigo']),
    )
    return jsonify(resultado), status


@auth_bp.route('/2fa/desactivar', methods=['POST'])
@jwt_required()
def desactivar_2fa():
    """
    Desactiva el 2FA verificando primero el código actual.
    No se puede desactivar sin el código.

    Body JSON:
    {
        "codigo": "123456"
    }
    """
    claims = get_jwt()
    usuario_id = claims.get('sub')
    data = request.get_json()

    if not data or not data.get('codigo'):
        return jsonify({'error': 'Campo requerido: codigo'}), 400

    db = next(get_db())
    use_case = ActivarDosFactoresUseCase(db=db)
    resultado, status = use_case.desactivar(
        usuario_id=usuario_id,
        codigo=str(data['codigo']),
    )
    return jsonify(resultado), status


@auth_bp.route('/2fa/verificar-login', methods=['POST'])
@limiter.limit('5 per minute')
@jwt_required()
def verificar_totp_login():
    """
    Segundo paso del login cuando 2FA está activo.
    Recibe el código TOTP y emite el JWT real si es correcto.

    Body JSON:
    {
        "codigo": "123456"
    }
    """
    claims = get_jwt()
    usuario_id = claims.get('sub')
    rol_id = claims.get('rol')
    perfil_id = claims.get('perfil_id')
    data = request.get_json()

    if not data or not data.get('codigo'):
        return jsonify({'error': 'Campo requerido: codigo'}), 400

    db = next(get_db())
    use_case = VerificarTOTPLoginUseCase(db=db)
    resultado, status = use_case.ejecutar(
        usuario_id=usuario_id,
        codigo=str(data['codigo']),
        rol_id=rol_id,
        perfil_id=perfil_id,
    )
    return jsonify(resultado), status


@auth_bp.route('/recuperar-password', methods=['POST'])
@limiter.limit('3 per hour')
def recuperar_password():
    """
    Solicita enlace de recuperación de contraseña.
    Limiter de 3 por hora para evitar spam de correos.

    Body JSON:
    {
        "correo": "usuario@email.com"
    }
    """
    data = request.get_json()

    if not data or not data.get('correo'):
        return jsonify({'error': 'Campo requerido: correo'}), 400

    db = next(get_db())
    use_case = RecuperarPasswordUseCase(db=db)

    resultado, status = use_case.ejecutar(
        correo=data['correo'],
        frontend_url=os.getenv('FRONTEND_URL', 'http://localhost:4200'),
    )
    return jsonify(resultado), status


@auth_bp.route('/reset-password', methods=['POST'])
@limiter.limit('5 per hour')
def reset_password():
    """
    Resetea la contraseña con el token del correo.

    Body JSON:
    {
        "token": "token-del-enlace",
        "nueva_password": "NuevaPass123!"
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Body JSON requerido'}), 400

    campos = ['token', 'nueva_password']
    for campo in campos:
        if campo not in data:
            return jsonify({
                'error': f'Campo requerido: {campo}'
            }), 400

    db = next(get_db())
    use_case = ResetearPasswordUseCase(db=db)

    resultado, status = use_case.ejecutar(
        token=data['token'],
        nueva_password=data['nueva_password'],
    )
    return jsonify(resultado), status


@auth_bp.route('/verificar-token-reset/<token>', methods=['GET'])
def verificar_token_reset(token):
    """
    Verifica si un token de reset es válido antes de mostrar
    el formulario de nueva contraseña en el frontend.
    El frontend llama esto cuando el usuario llega desde el enlace.
    """
    db = next(get_db())

    row = db.execute(
        text("""
            SELECT id, nombre
            FROM usuarios
            WHERE reset_password_token = :token
              AND reset_password_expira > NOW()
              AND activo = TRUE
        """),
        {'token': token}
    ).fetchone()

    if not row:
        return jsonify({
            'valido': False,
            'error': 'El enlace expiró o ya fue usado.'
        }), 400

    return jsonify({
        'valido': True,
        'nombre': row.nombre,
    }), 200