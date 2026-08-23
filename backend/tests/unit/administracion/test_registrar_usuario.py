"""
Tests unitarios — RegistrarUsuarioUseCase
CU-ADM-001: Gestionar Usuarios (flujo de creacion)

Valida:
- Hash bcrypt de la password antes de persistir
- Deteccion de correo duplicado
- Creacion automatica de perfil segun rol
- Validaciones de negocio para agronomo (numero de registro)

Patron AAA: Arrange / Act / Assert
Sin base de datos — todo mockeado.
"""
import pytest
import bcrypt
from unittest.mock import MagicMock, call
from app.application.use_cases.administracion.registrar_usuario import (
    RegistrarUsuarioUseCase
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def repo_usuario():
    mock = MagicMock()
    mock.existe_correo.return_value = False
    return mock


@pytest.fixture
def repo_agricultor():
    return MagicMock()


@pytest.fixture
def repo_agronomo():
    return MagicMock()


@pytest.fixture
def caso_uso(repo_usuario, repo_agricultor, repo_agronomo):
    return RegistrarUsuarioUseCase(
        usuario_repository=repo_usuario,
        agricultor_repository=repo_agricultor,
        agronomo_repository=repo_agronomo,
    )


def usuario_guardado_mock(rol_id=2):
    usuario = MagicMock()
    usuario.id = 'uuid-nuevo-usuario'
    usuario.nombre = 'Cesar'
    usuario.apellido = 'Ramos'
    usuario.correo = 'cesar511ramos@gmail.com'
    usuario.rol_id = rol_id
    usuario.activo = True
    usuario.nombre_completo.return_value = 'Cesar Ramos'
    return usuario


# ============================================================
# Tests — Registro exitoso agricultor
# ============================================================

class TestRegistroExitosoAgricultor:
    def test_registro_retorna_datos_del_usuario(
        self, caso_uso, repo_usuario, repo_agricultor
    ):
        # Arrange
        repo_usuario.guardar.return_value = usuario_guardado_mock(rol_id=2)

        # Act
        resultado = caso_uso.ejecutar(
            nombre='Cesar',
            apellido='Ramos',
            correo='cesar511ramos@gmail.com',
            password='Agrocycle2026!',
            rol_id=2,
        )

        # Assert
        assert resultado['correo'] == 'cesar511ramos@gmail.com'
        assert resultado['rol_id'] == 2
        assert resultado['activo'] is True

    def test_registro_agricultor_crea_perfil_en_agricultores(
        self, caso_uso, repo_usuario, repo_agricultor
    ):
        # Arrange
        usuario = usuario_guardado_mock(rol_id=2)
        repo_usuario.guardar.return_value = usuario

        # Act
        caso_uso.ejecutar(
            nombre='Cesar',
            apellido='Ramos',
            correo='cesar511ramos@gmail.com',
            password='Agrocycle2026!',
            rol_id=2,
        )

        # Assert — debe crear perfil de agricultor
        repo_agricultor.crear.assert_called_once_with(usuario.id)

    def test_registro_agricultor_no_crea_perfil_agronomo(
        self, caso_uso, repo_usuario, repo_agronomo
    ):
        # Arrange
        repo_usuario.guardar.return_value = usuario_guardado_mock(rol_id=2)

        # Act
        caso_uso.ejecutar(
            nombre='Cesar',
            apellido='Ramos',
            correo='cesar511ramos@gmail.com',
            password='Agrocycle2026!',
            rol_id=2,
        )

        # Assert
        repo_agronomo.crear.assert_not_called()

    def test_correo_se_normaliza_a_minusculas(
        self, caso_uso, repo_usuario
    ):
        """El correo debe almacenarse siempre en minusculas."""
        # Arrange
        repo_usuario.guardar.return_value = usuario_guardado_mock()

        # Act
        caso_uso.ejecutar(
            nombre='Cesar',
            apellido='Ramos',
            correo='CESAR511RAMOS@GMAIL.COM',
            password='Agrocycle2026!',
            rol_id=2,
        )

        # Assert — verificar que se llamó existe_correo con el correo
        repo_usuario.existe_correo.assert_called_once_with(
            'CESAR511RAMOS@GMAIL.COM'
        )
        # El usuario guardado debe tener el correo en minusculas
        usuario_creado = repo_usuario.guardar.call_args[0][0]
        assert usuario_creado.correo == 'cesar511ramos@gmail.com'


# ============================================================
# Tests — Hash de password
# ============================================================

class TestHashPassword:
    """
    La password nunca debe almacenarse en texto plano.
    bcrypt con rounds=12 es el estandar de seguridad del sistema.
    """

    def test_password_se_guarda_hasheada_no_en_texto_plano(
        self, caso_uso, repo_usuario
    ):
        # Arrange
        repo_usuario.guardar.return_value = usuario_guardado_mock()
        password_original = 'Agrocycle2026!'

        # Act
        caso_uso.ejecutar(
            nombre='Cesar',
            apellido='Ramos',
            correo='cesar511ramos@gmail.com',
            password=password_original,
            rol_id=2,
        )

        # Assert — el usuario guardado no debe tener la password en texto plano
        usuario_guardado = repo_usuario.guardar.call_args[0][0]
        assert usuario_guardado.password_hash != password_original

    def test_password_hash_es_verificable_con_bcrypt(
        self, caso_uso, repo_usuario
    ):
        """
        El hash generado debe poder verificarse con bcrypt.checkpw
        — es la misma funcion que usa AutenticarUsuarioUseCase.
        """
        # Arrange
        repo_usuario.guardar.return_value = usuario_guardado_mock()
        password_original = 'Agrocycle2026!'

        # Act
        caso_uso.ejecutar(
            nombre='Cesar',
            apellido='Ramos',
            correo='cesar511ramos@gmail.com',
            password=password_original,
            rol_id=2,
        )

        # Assert
        usuario_guardado = repo_usuario.guardar.call_args[0][0]
        es_valida = bcrypt.checkpw(
            password_original.encode('utf-8'),
            usuario_guardado.password_hash.encode('utf-8')
        )
        assert es_valida is True

    def test_password_incorrecta_no_verifica_contra_hash(
        self, caso_uso, repo_usuario
    ):
        # Arrange
        repo_usuario.guardar.return_value = usuario_guardado_mock()

        # Act
        caso_uso.ejecutar(
            nombre='Cesar',
            apellido='Ramos',
            correo='cesar511ramos@gmail.com',
            password='Agrocycle2026!',
            rol_id=2,
        )

        # Assert
        usuario_guardado = repo_usuario.guardar.call_args[0][0]
        es_valida = bcrypt.checkpw(
            'password_incorrecta'.encode('utf-8'),
            usuario_guardado.password_hash.encode('utf-8')
        )
        assert es_valida is False

    def test_dos_registros_del_mismo_password_generan_hashes_distintos(
        self, caso_uso, repo_usuario
    ):
        """
        bcrypt genera un salt aleatorio en cada llamada.
        Dos hashes del mismo password NUNCA deben ser iguales.
        Esto protege contra ataques de rainbow table.
        """
        # Arrange
        repo_usuario.guardar.side_effect = [
            usuario_guardado_mock(), usuario_guardado_mock()
        ]

        # Act
        caso_uso.ejecutar('A', 'B', 'a@test.com', 'MismaPassword123!', 2)
        caso_uso.ejecutar('C', 'D', 'c@test.com', 'MismaPassword123!', 2)

        # Assert
        llamadas = repo_usuario.guardar.call_args_list
        hash1 = llamadas[0][0][0].password_hash
        hash2 = llamadas[1][0][0].password_hash
        assert hash1 != hash2


# ============================================================
# Tests — Correo duplicado
# ============================================================

class TestCorreoDuplicado:
    def test_correo_duplicado_lanza_error(self, caso_uso, repo_usuario):
        # Arrange
        repo_usuario.existe_correo.return_value = True

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            caso_uso.ejecutar(
                nombre='Otro',
                apellido='Usuario',
                correo='cesar511ramos@gmail.com',
                password='OtroPassword123!',
                rol_id=2,
            )
        assert 'registrado' in str(exc.value).lower()

    def test_correo_duplicado_no_guarda_usuario(
        self, caso_uso, repo_usuario
    ):
        # Arrange
        repo_usuario.existe_correo.return_value = True

        # Act
        with pytest.raises(ValueError):
            caso_uso.ejecutar(
                nombre='Otro',
                apellido='Usuario',
                correo='cesar511ramos@gmail.com',
                password='OtroPassword123!',
                rol_id=2,
            )

        # Assert — nunca debe llamar a guardar
        repo_usuario.guardar.assert_not_called()

    def test_correo_duplicado_no_crea_perfil(
        self, caso_uso, repo_usuario, repo_agricultor
    ):
        # Arrange
        repo_usuario.existe_correo.return_value = True

        # Act
        with pytest.raises(ValueError):
            caso_uso.ejecutar(
                nombre='Otro',
                apellido='Usuario',
                correo='cesar511ramos@gmail.com',
                password='OtroPassword123!',
                rol_id=2,
            )

        # Assert
        repo_agricultor.crear.assert_not_called()


# ============================================================
# Tests — Registro agronomo
# ============================================================

class TestRegistroAgronomo:
    def test_agronomo_sin_numero_registro_lanza_error(
        self, caso_uso, repo_usuario
    ):
        # Arrange
        repo_usuario.existe_correo.return_value = False

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            caso_uso.ejecutar(
                nombre='Carlos',
                apellido='Lopez',
                correo='agronomo@agrocycle.ec',
                password='Agronomo2026!',
                rol_id=3,
                numero_registro=None,
            )
        assert 'registro' in str(exc.value).lower()

    def test_agronomo_con_numero_registro_crea_perfil_agronomo(
        self, caso_uso, repo_usuario, repo_agronomo
    ):
        # Arrange
        usuario = usuario_guardado_mock(rol_id=3)
        repo_usuario.guardar.return_value = usuario

        # Act
        caso_uso.ejecutar(
            nombre='Carlos',
            apellido='Lopez',
            correo='agronomo@agrocycle.ec',
            password='Agronomo2026!',
            rol_id=3,
            numero_registro='ING-AGR-001',
            especialidad='Cultivos tropicales',
        )

        # Assert
        repo_agronomo.crear.assert_called_once_with(
            usuario_id=usuario.id,
            numero_registro='ING-AGR-001',
            especialidad='Cultivos tropicales',
        )

    def test_agronomo_no_crea_perfil_agricultor(
        self, caso_uso, repo_usuario, repo_agricultor
    ):
        # Arrange
        repo_usuario.guardar.return_value = usuario_guardado_mock(rol_id=3)

        # Act
        caso_uso.ejecutar(
            nombre='Carlos',
            apellido='Lopez',
            correo='agronomo@agrocycle.ec',
            password='Agronomo2026!',
            rol_id=3,
            numero_registro='ING-AGR-001',
        )

        # Assert
        repo_agricultor.crear.assert_not_called()
