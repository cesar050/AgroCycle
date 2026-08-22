"""
Caso de uso: Activar autenticación de dos factores (2FA).

Flujo:
1. Usuario solicita activar 2FA
2. Sistema genera secreto y retorna QR
3. Usuario escanea QR y envía código de confirmación
4. Sistema verifica y activa 2FA definitivamente
"""
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.infrastructure.security.totp_service import TOTPService
from app.infrastructure.logging.logger import log_caso_de_uso


class ActivarDosFactoresUseCase:
    """
    Gestiona la activación del 2FA en dos pasos:
    - Paso 1: generar QR
    - Paso 2: confirmar con código y activar
    """

    def __init__(self, db: Session):
        self.db = db
        self.totp = TOTPService()

    @log_caso_de_uso('Activar 2FA - Paso 1: Generar QR')
    def generar_qr(self, usuario_id: str) -> tuple:
        """
        Paso 1 — Genera el secreto y retorna el QR para escanear.

        El secreto se guarda en BD pero totp_activo sigue en False
        hasta que el usuario confirme con el código.

        Args:
            usuario_id: UUID del usuario autenticado

        Returns:
            tuple (dict con QR, int código HTTP)
        """
        usuario = self._obtener_usuario(usuario_id)

        if not usuario:
            return {'error': 'Usuario no encontrado'}, 404

        if usuario['totp_activo']:
            return {
                'error': 'El 2FA ya está activado en tu cuenta. '
                         'Desactívalo primero si quieres reconfigurarlo.'
            }, 400

        # Generar nuevo secreto
        secreto = self.totp.generar_secreto()

        # Guardar secreto en BD — aún no está activo
        self.db.execute(
            text("""
                UPDATE usuarios
                SET totp_secret = :secreto,
                    totp_activo = FALSE,
                    totp_verificado = FALSE
                WHERE id = CAST(:usuario_id AS uuid)
            """),
            {'secreto': secreto, 'usuario_id': usuario_id}
        )
        self.db.commit()

        # Generar QR
        qr_base64 = self.totp.generar_qr_base64(
            secreto=secreto,
            correo=usuario['correo'],
        )

        return {
            'mensaje': 'Escanea el código QR con Google Authenticator o Authy. '
                       'Luego ingresa el código de 6 dígitos para confirmar.',
            'qr_imagen': qr_base64,
            'instrucciones': [
                '1. Abre Google Authenticator o Authy en tu teléfono',
                '2. Toca el botón + para agregar una cuenta',
                '3. Escanea el código QR',
                '4. Ingresa el código de 6 dígitos que aparece en la app',
            ]
        }, 200

    @log_caso_de_uso('Activar 2FA - Paso 2: Confirmar código')
    def confirmar_activacion(
        self, usuario_id: str, codigo: str
    ) -> tuple:
        """
        Paso 2 — Verifica el código e activa el 2FA definitivamente.

        Si el código es correcto activa totp_activo = True.
        A partir de este momento el login pedirá el código.

        Args:
            usuario_id: UUID del usuario
            codigo: código de 6 dígitos de la app autenticadora

        Returns:
            tuple (dict resultado, int código HTTP)
        """
        usuario = self._obtener_usuario(usuario_id)

        if not usuario:
            return {'error': 'Usuario no encontrado'}, 404

        if not usuario['totp_secret']:
            return {
                'error': 'Primero genera el QR antes de confirmar.'
            }, 400

        if usuario['totp_activo']:
            return {'error': 'El 2FA ya está activado.'}, 400

        # Verificar el código
        es_valido = self.totp.verificar_codigo(
            secreto=usuario['totp_secret'],
            codigo=codigo,
        )

        if not es_valido:
            return {
                'error': 'Código incorrecto. Verifica que la hora de tu '
                         'teléfono esté sincronizada e intenta de nuevo.'
            }, 400

        # Activar 2FA
        self.db.execute(
            text("""
                UPDATE usuarios
                SET totp_activo = TRUE,
                    totp_verificado = TRUE
                WHERE id = CAST(:usuario_id AS uuid)
            """),
            {'usuario_id': usuario_id}
        )
        self.db.commit()

        return {
            'mensaje': 'Autenticación de dos factores activada correctamente. '
                       'Desde ahora necesitarás el código de tu app para iniciar sesión.',
            'totp_activo': True,
        }, 200

    @log_caso_de_uso('Desactivar 2FA')
    def desactivar(
        self, usuario_id: str, codigo: str
    ) -> tuple:
        """
        Desactiva el 2FA verificando primero el código actual.
        No se puede desactivar sin el código — evita que alguien
        que roba la contraseña desactive el 2FA.

        Args:
            usuario_id: UUID del usuario
            codigo: código de 6 dígitos para confirmar la desactivación

        Returns:
            tuple (dict resultado, int código HTTP)
        """
        usuario = self._obtener_usuario(usuario_id)

        if not usuario:
            return {'error': 'Usuario no encontrado'}, 404

        if not usuario['totp_activo']:
            return {'error': 'El 2FA no está activado.'}, 400

        es_valido = self.totp.verificar_codigo(
            secreto=usuario['totp_secret'],
            codigo=codigo,
        )

        if not es_valido:
            return {
                'error': 'Código incorrecto. No se pudo desactivar el 2FA.'
            }, 400

        self.db.execute(
            text("""
                UPDATE usuarios
                SET totp_activo = FALSE,
                    totp_verificado = FALSE,
                    totp_secret = NULL
                WHERE id = CAST(:usuario_id AS uuid)
            """),
            {'usuario_id': usuario_id}
        )
        self.db.commit()

        return {
            'mensaje': 'Autenticación de dos factores desactivada correctamente.',
            'totp_activo': False,
        }, 200

    def _obtener_usuario(self, usuario_id: str) -> dict:
        """Obtiene datos del usuario necesarios para el 2FA."""
        row = self.db.execute(
            text("""
                SELECT id, correo, totp_secret, totp_activo, totp_verificado
                FROM usuarios
                WHERE id = CAST(:usuario_id AS uuid)
            """),
            {'usuario_id': usuario_id}
        ).fetchone()

        if not row:
            return None

        return {
            'id': str(row.id),
            'correo': row.correo,
            'totp_secret': row.totp_secret,
            'totp_activo': row.totp_activo,
            'totp_verificado': row.totp_verificado,
        }