"""
Servicio TOTP (Time-based One-Time Password) para AgroCycle.

Implementa autenticación de dos factores usando el estándar RFC 6238.
El agricultor escanea un QR con Google Authenticator o Authy
y cada 30 segundos obtiene un código de 6 dígitos.

Flujo completo:
1. Agricultor activa 2FA → sistema genera secreto y QR
2. Agricultor escanea QR con su app de autenticación
3. Agricultor ingresa el código de 6 dígitos para confirmar
4. Sistema marca totp_verificado = True
5. En el login: si totp_activo, pide el código además de la contraseña
"""
import pyotp
import qrcode
import io
import base64


NOMBRE_EMISOR = 'AgroCycle'


class TOTPService:
    """
    Encapsula toda la lógica TOTP para no mezclarla
    con los casos de uso de negocio.
    """

    def generar_secreto(self) -> str:
        """
        Genera un secreto aleatorio de 32 caracteres en base32.
        Este secreto se guarda en la BD y nunca se muestra de nuevo
        al usuario — solo el QR al momento de activación.
        """
        return pyotp.random_base32()

    def generar_uri(self, secreto: str, correo: str) -> str:
        """
        Genera la URI otpauth:// que el QR codifica.
        Google Authenticator y Authy leen esta URI para configurar
        la cuenta automáticamente al escanear el QR.

        Args:
            secreto: secreto base32 generado por generar_secreto()
            correo: correo del usuario, se muestra en la app

        Returns:
            URI en formato otpauth://totp/...
        """
        totp = pyotp.TOTP(secreto)
        return totp.provisioning_uri(
            name=correo,
            issuer_name=NOMBRE_EMISOR,
        )

    def generar_qr_base64(self, secreto: str, correo: str) -> str:
        """
        Genera el QR como imagen PNG en base64.
        El frontend puede mostrarlo directamente en un <img>
        sin necesitar archivos temporales.

        Returns:
            String base64 con prefijo data:image/png;base64,...
        """
        uri = self.generar_uri(secreto, correo)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=8,
            border=2,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        imagen = qr.make_image(fill_color='black', back_color='white')

        buffer = io.BytesIO()
        imagen.save(buffer, format='PNG')
        buffer.seek(0)

        imagen_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        return f"data:image/png;base64,{imagen_base64}"

    def verificar_codigo(self, secreto: str, codigo: str) -> bool:
        """
        Verifica que el código de 6 dígitos es válido.

        Acepta códigos del intervalo actual y los dos anteriores
        para compensar diferencias de reloj entre el servidor
        y el dispositivo del usuario (ventana de ±30 segundos).

        Args:
            secreto: secreto base32 guardado en la BD
            codigo: código de 6 dígitos ingresado por el usuario

        Returns:
            True si el código es válido, False si no
        """
        if not secreto or not codigo:
            return False

        totp = pyotp.TOTP(secreto)
        # valid_window=1 acepta el código actual y el anterior
        return totp.verify(codigo, valid_window=1)