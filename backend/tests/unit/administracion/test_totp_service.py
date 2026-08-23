"""
Tests unitarios — TOTPService
Valida la autenticacion de dos factores (2FA) con TOTP RFC 6238.

El 2FA es obligatorio para administradores en AgroCycle.
Estos tests validan que el servicio genere secretos validos,
URIs correctas y verifique codigos de forma segura.

Patron AAA: Arrange / Act / Assert
No requiere base de datos ni mocks — el servicio es puro.
"""
import pytest
import pyotp
from app.infrastructure.security.totp_service import TOTPService, NOMBRE_EMISOR


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def servicio():
    return TOTPService()


@pytest.fixture
def secreto_valido(servicio):
    return servicio.generar_secreto()


# ============================================================
# Tests — Generacion de secreto
# ============================================================

class TestGenerarSecreto:
    """
    El secreto es la semilla del TOTP.
    Debe ser aleatorio, en formato base32 y de longitud suficiente.
    """

    def test_secreto_no_es_vacio(self, servicio):
        assert servicio.generar_secreto() != ''

    def test_secreto_es_base32_valido(self, servicio):
        """pyotp debe poder usar el secreto sin lanzar excepcion."""
        secreto = servicio.generar_secreto()
        totp = pyotp.TOTP(secreto)
        assert totp is not None

    def test_dos_secretos_consecutivos_son_distintos(self, servicio):
        """Cada llamada debe generar un secreto diferente."""
        secreto1 = servicio.generar_secreto()
        secreto2 = servicio.generar_secreto()
        assert secreto1 != secreto2

    def test_secreto_tiene_longitud_minima_segura(self, servicio):
        """Un secreto base32 seguro debe tener al menos 16 caracteres."""
        secreto = servicio.generar_secreto()
        assert len(secreto) >= 16

    def test_secreto_solo_contiene_caracteres_base32(self, servicio):
        """Base32 usa solo A-Z y 2-7 mas el padding con =."""
        import re
        secreto = servicio.generar_secreto()
        assert re.match(r'^[A-Z2-7=]+$', secreto)


# ============================================================
# Tests — Generacion de URI
# ============================================================

class TestGenerarUri:
    def test_uri_comienza_con_otpauth(self, servicio, secreto_valido):
        uri = servicio.generar_uri(secreto_valido, 'cesar511ramos@gmail.com')
        assert uri.startswith('otpauth://totp/')

    def test_uri_contiene_nombre_emisor_agrocycle(self, servicio, secreto_valido):
        uri = servicio.generar_uri(secreto_valido, 'cesar511ramos@gmail.com')
        assert NOMBRE_EMISOR in uri

    def test_uri_contiene_correo_del_usuario(self, servicio, secreto_valido):
        correo = 'cesar511ramos@gmail.com'
        uri = servicio.generar_uri(secreto_valido, correo)
        assert 'cesar511ramos' in uri

    def test_uri_contiene_el_secreto(self, servicio, secreto_valido):
        uri = servicio.generar_uri(secreto_valido, 'test@test.com')
        assert secreto_valido in uri

    def test_distintos_correos_generan_distintas_uris(
        self, servicio, secreto_valido
    ):
        uri1 = servicio.generar_uri(secreto_valido, 'usuario1@test.com')
        uri2 = servicio.generar_uri(secreto_valido, 'usuario2@test.com')
        assert uri1 != uri2


# ============================================================
# Tests — Generacion de QR
# ============================================================

class TestGenerarQr:
    def test_qr_comienza_con_prefijo_data_image(
        self, servicio, secreto_valido
    ):
        qr = servicio.generar_qr_base64(
            secreto_valido, 'cesar511ramos@gmail.com'
        )
        assert qr.startswith('data:image/png;base64,')

    def test_qr_no_es_vacio(self, servicio, secreto_valido):
        qr = servicio.generar_qr_base64(
            secreto_valido, 'cesar511ramos@gmail.com'
        )
        assert len(qr) > 100

    def test_qr_es_base64_valido(self, servicio, secreto_valido):
        """El contenido base64 debe poder decodificarse."""
        import base64
        qr = servicio.generar_qr_base64(
            secreto_valido, 'cesar511ramos@gmail.com'
        )
        contenido_base64 = qr.replace('data:image/png;base64,', '')
        datos = base64.b64decode(contenido_base64)
        assert len(datos) > 0

    def test_qr_decodificado_es_imagen_png(self, servicio, secreto_valido):
        """Los primeros bytes de un PNG son siempre la firma PNG."""
        import base64
        PNG_SIGNATURE = b'\x89PNG'
        qr = servicio.generar_qr_base64(
            secreto_valido, 'cesar511ramos@gmail.com'
        )
        contenido = base64.b64decode(
            qr.replace('data:image/png;base64,', '')
        )
        assert contenido[:4] == PNG_SIGNATURE


# ============================================================
# Tests — Verificacion de codigo TOTP
# ============================================================

class TestVerificarCodigo:
    """
    Valida la verificacion de codigos TOTP de 6 digitos.
    El codigo valido para el secreto actual se genera con pyotp
    para no depender de un valor hardcodeado que expira en 30 segundos.
    """

    def test_codigo_valido_retorna_true(self, servicio, secreto_valido):
        # Arrange — generar el codigo actual con el mismo secreto
        totp = pyotp.TOTP(secreto_valido)
        codigo_actual = totp.now()

        # Act
        resultado = servicio.verificar_codigo(secreto_valido, codigo_actual)

        # Assert
        assert resultado is True

    def test_codigo_incorrecto_retorna_false(self, servicio, secreto_valido):
        # Act
        resultado = servicio.verificar_codigo(secreto_valido, '000000')

        # Assert
        assert resultado is False

    def test_codigo_vacio_retorna_false(self, servicio, secreto_valido):
        assert servicio.verificar_codigo(secreto_valido, '') is False

    def test_secreto_vacio_retorna_false(self, servicio):
        assert servicio.verificar_codigo('', '123456') is False

    def test_ninguno_vacio_con_secreto_invalido_retorna_false(self, servicio):
        assert servicio.verificar_codigo('SECRETO_INVALIDO', '123456') is False

    def test_codigo_de_otro_secreto_no_verifica(self, servicio):
        """Un codigo generado con el secreto A no debe verificar con el secreto B."""
        secreto_a = servicio.generar_secreto()
        secreto_b = servicio.generar_secreto()
        codigo_de_a = pyotp.TOTP(secreto_a).now()
        assert servicio.verificar_codigo(secreto_b, codigo_de_a) is False

    def test_codigo_tiene_exactamente_6_digitos(self, servicio, secreto_valido):
        """El codigo TOTP RFC 6238 siempre tiene 6 digitos."""
        totp = pyotp.TOTP(secreto_valido)
        codigo = totp.now()
        assert len(codigo) == 6
        assert codigo.isdigit()

    def test_codigo_numerico_como_string_verifica_correctamente(
        self, servicio, secreto_valido
    ):
        """El codigo se recibe como string desde el frontend."""
        totp = pyotp.TOTP(secreto_valido)
        codigo = totp.now()
        assert isinstance(codigo, str)
        assert servicio.verificar_codigo(secreto_valido, codigo) is True
