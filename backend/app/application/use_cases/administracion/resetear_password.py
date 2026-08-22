"""
Caso de uso: Resetear contraseña con token de recuperación.

El usuario llegó desde el enlace del correo, ingresó
su nueva contraseña y el frontend envía el token + nueva clave.
"""
import bcrypt
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.infrastructure.logging.logger import log_caso_de_uso


class ResetearPasswordUseCase:

    def __init__(self, db: Session):
        self.db = db

    @log_caso_de_uso('Resetear Password')
    def ejecutar(
        self, token: str, nueva_password: str
    ) -> tuple:
        """
        Verifica el token y actualiza la contraseña.

        Args:
            token: token recibido del enlace del correo
            nueva_password: nueva contraseña del usuario

        Returns:
            tuple (dict, int)
        """
        # 1. Buscar usuario con ese token válido y no expirado
        usuario = self._buscar_por_token(token)

        if not usuario:
            return {
                'error': 'El enlace de recuperación es inválido o expiró. '
                         'Solicita uno nuevo desde la pantalla de login.'
            }, 400

        # 2. Validar nueva contraseña
        error_password = self._validar_password(nueva_password)
        if error_password:
            return {'error': error_password}, 400

        # 3. Hashear nueva contraseña
        password_hash = bcrypt.hashpw(
            nueva_password.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')

        # 4. Actualizar contraseña y limpiar token
        self.db.execute(
            text("""
                UPDATE usuarios
                SET password_hash         = :password_hash,
                    reset_password_token  = NULL,
                    reset_password_expira = NULL,
                    intentos_fallidos     = 0,
                    bloqueado_hasta       = NULL
                WHERE id = CAST(:usuario_id AS uuid)
            """),
            {
                'password_hash': password_hash,
                'usuario_id': usuario['id'],
            }
        )
        self.db.commit()

        return {
            'mensaje': 'Contraseña actualizada correctamente. '
                       'Ya puedes iniciar sesión con tu nueva contraseña.'
        }, 200

    def _buscar_por_token(self, token: str) -> dict:
        """
        Busca usuario por token de reset válido y no expirado.
        Un token expirado se trata igual que uno inválido.
        """
        row = self.db.execute(
            text("""
                SELECT id, nombre, correo
                FROM usuarios
                WHERE reset_password_token = :token
                  AND reset_password_expira > NOW()
                  AND activo = TRUE
            """),
            {'token': token}
        ).fetchone()

        if not row:
            return None

        return {
            'id': str(row.id),
            'nombre': row.nombre,
            'correo': row.correo,
        }

    def _validar_password(self, password: str) -> str:
        """
        Valida que la nueva contraseña cumple los requisitos.
        Retorna mensaje de error o None si es válida.
        """
        if len(password) < 8:
            return 'La contraseña debe tener al menos 8 caracteres.'

        if not any(c.isupper() for c in password):
            return 'La contraseña debe tener al menos una letra mayúscula.'

        if not any(c.isdigit() for c in password):
            return 'La contraseña debe tener al menos un número.'

        return None