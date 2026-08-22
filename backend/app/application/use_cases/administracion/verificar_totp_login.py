"""
Caso de uso: Verificar código TOTP durante el login.

Cuando el usuario tiene 2FA activo el login se hace en dos pasos:
1. POST /login → verifica correo y contraseña → retorna token temporal
2. POST /login/verificar-2fa → verifica código TOTP → retorna JWT real

El token temporal dura 5 minutos — tiempo suficiente para
abrir la app y copiar el código.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from flask_jwt_extended import create_access_token, create_refresh_token

from app.infrastructure.security.totp_service import TOTPService
from app.infrastructure.logging.logger import log_caso_de_uso


class VerificarTOTPLoginUseCase:
    """
    Segundo paso del login cuando 2FA está activo.
    Recibe el usuario_id del token temporal y el código TOTP.
    """

    def __init__(self, db: Session):
        self.db = db
        self.totp = TOTPService()

    @log_caso_de_uso('Verificar TOTP en Login')
    def ejecutar(
        self,
        usuario_id: str,
        codigo: str,
        rol_id: int,
        perfil_id: str,
    ) -> tuple:
        """
        Verifica el código TOTP y si es correcto emite el JWT real.

        Args:
            usuario_id: UUID del usuario (del token temporal)
            codigo: código de 6 dígitos ingresado por el usuario
            rol_id: rol del usuario para el JWT enriquecido
            perfil_id: perfil_id para el JWT enriquecido

        Returns:
            tuple (dict con tokens, int código HTTP)
        """
        # Obtener secreto TOTP del usuario
        row = self.db.execute(
            text("""
                SELECT totp_secret, totp_activo, nombre, apellido, correo
                FROM usuarios
                WHERE id = CAST(:usuario_id AS uuid)
                  AND totp_activo = TRUE
            """),
            {'usuario_id': usuario_id}
        ).fetchone()

        if not row:
            return {
                'error': 'Usuario no encontrado o 2FA no está activado.'
            }, 404

        # Verificar el código
        es_valido = self.totp.verificar_codigo(
            secreto=row.totp_secret,
            codigo=codigo,
        )

        if not es_valido:
            return {
                'error': 'Código de verificación incorrecto o expirado. '
                         'Los códigos cambian cada 30 segundos.'
            }, 401

        # Código correcto — emitir JWT real
        additional_claims = {
            'rol': rol_id,
            'perfil_id': perfil_id,
        }

        access_token = create_access_token(
            identity=usuario_id,
            additional_claims=additional_claims,
        )
        refresh_token = create_refresh_token(
            identity=usuario_id,
            additional_claims=additional_claims,
        )

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'usuario': {
                'id': usuario_id,
                'nombre': f"{row.nombre} {row.apellido}",
                'correo': row.correo,
                'rol_id': rol_id,
            },
            'mensaje': 'Autenticación completada exitosamente.',
        }, 200