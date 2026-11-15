"""
Tests unitarios — GestionarParcelasUseCase
Valida la cadena de propiedad parcela -> lote -> finca -> agricultor,
y que eliminar() nunca bloquea (la parcela es una hoja del arbol).
"""
import pytest
from unittest.mock import MagicMock
from app.application.use_cases.fincas_parcelas.gestionar_parcelas import GestionarParcelasUseCase
from app.domain.entities.finca import Finca
from app.domain.entities.lote import Lote
from app.domain.entities.parcela import Parcela

AGRICULTOR_ID = 'agricultor-1'
OTRO_AGRICULTOR_ID = 'agricultor-2'


@pytest.fixture
def parcela_repo():
    return MagicMock()


@pytest.fixture
def lote_repo():
    return MagicMock()


@pytest.fixture
def finca_repo():
    return MagicMock()


@pytest.fixture
def caso_uso(parcela_repo, lote_repo, finca_repo):
    return GestionarParcelasUseCase(parcela_repo, lote_repo, finca_repo)


def _parcela():
    return Parcela(lote_id='lote-1', nombre='Parcela Test', id='parcela-1')


def _lote():
    return Lote(finca_id='finca-1', nombre='Lote Test', id='lote-1')


def _finca(agricultor_id=AGRICULTOR_ID):
    return Finca(agricultor_id=agricultor_id, nombre='Finca Test', id='finca-1')


class TestListarParcelas:
    def test_listar_lote_de_otro_agricultor_lanza_permission_error(self, caso_uso, lote_repo, finca_repo):
        lote_repo.buscar_por_id.return_value = _lote()
        finca_repo.buscar_por_id.return_value = _finca(agricultor_id=OTRO_AGRICULTOR_ID)
        with pytest.raises(PermissionError):
            caso_uso.listar('lote-1', AGRICULTOR_ID)


class TestEliminarParcela:
    def test_parcela_no_encontrada_lanza_value_error(self, caso_uso, parcela_repo):
        parcela_repo.buscar_por_id.return_value = None
        with pytest.raises(ValueError):
            caso_uso.eliminar('parcela-1', AGRICULTOR_ID)

    def test_parcela_de_otro_agricultor_lanza_permission_error(
        self, caso_uso, parcela_repo, lote_repo, finca_repo
    ):
        parcela_repo.buscar_por_id.return_value = _parcela()
        lote_repo.buscar_por_id.return_value = _lote()
        finca_repo.buscar_por_id.return_value = _finca(agricultor_id=OTRO_AGRICULTOR_ID)
        with pytest.raises(PermissionError):
            caso_uso.eliminar('parcela-1', AGRICULTOR_ID)

    def test_parcela_propia_se_marca_inactiva_sin_bloqueo(
        self, caso_uso, parcela_repo, lote_repo, finca_repo
    ):
        parcela = _parcela()
        parcela_repo.buscar_por_id.return_value = parcela
        lote_repo.buscar_por_id.return_value = _lote()
        finca_repo.buscar_por_id.return_value = _finca()
        parcela_repo.actualizar.side_effect = lambda p: p

        resultado = caso_uso.eliminar('parcela-1', AGRICULTOR_ID)

        assert parcela.activo is False
        assert resultado['activo'] is False


class TestEditarParcela:
    def test_editar_no_toca_geometria_ni_topografia(
        self, caso_uso, parcela_repo, lote_repo, finca_repo
    ):
        parcela = _parcela()
        parcela.pendiente_porcentaje = 12.5
        parcela_repo.buscar_por_id.return_value = parcela
        lote_repo.buscar_por_id.return_value = _lote()
        finca_repo.buscar_por_id.return_value = _finca()
        parcela_repo.actualizar.side_effect = lambda p: p

        resultado = caso_uso.editar('parcela-1', AGRICULTOR_ID, {'observaciones': 'nota'})

        assert parcela.observaciones == 'nota'
        assert resultado['pendiente_porcentaje'] == 12.5
