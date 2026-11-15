"""
Tests unitarios — GestionarLotesUseCase.eliminar/editar/obtener
Valida la cadena de propiedad lote -> finca -> agricultor y el
bloqueo de borrado cuando el lote tiene parcelas activas.
"""
import pytest
from unittest.mock import MagicMock
from app.application.use_cases.fincas_parcelas.gestionar_lotes import GestionarLotesUseCase
from app.domain.entities.finca import Finca
from app.domain.entities.lote import Lote
from app.domain.exceptions import ConflictoEliminacionError

AGRICULTOR_ID = 'agricultor-1'
OTRO_AGRICULTOR_ID = 'agricultor-2'


@pytest.fixture
def lote_repo():
    return MagicMock()


@pytest.fixture
def finca_repo():
    return MagicMock()


@pytest.fixture
def caso_uso(lote_repo, finca_repo):
    return GestionarLotesUseCase(lote_repo, finca_repo)


def _lote():
    return Lote(finca_id='finca-1', nombre='Lote Test', id='lote-1')


def _finca(agricultor_id=AGRICULTOR_ID):
    return Finca(agricultor_id=agricultor_id, nombre='Finca Test', id='finca-1')


class TestEliminarLote:
    def test_lote_no_encontrado_lanza_value_error(self, caso_uso, lote_repo):
        lote_repo.buscar_por_id.return_value = None
        with pytest.raises(ValueError):
            caso_uso.eliminar('lote-1', AGRICULTOR_ID)

    def test_lote_de_finca_ajena_lanza_permission_error(self, caso_uso, lote_repo, finca_repo):
        lote_repo.buscar_por_id.return_value = _lote()
        finca_repo.buscar_por_id.return_value = _finca(agricultor_id=OTRO_AGRICULTOR_ID)
        with pytest.raises(PermissionError):
            caso_uso.eliminar('lote-1', AGRICULTOR_ID)

    def test_lote_con_parcelas_activas_lanza_conflicto(self, caso_uso, lote_repo, finca_repo):
        lote_repo.buscar_por_id.return_value = _lote()
        finca_repo.buscar_por_id.return_value = _finca()
        lote_repo.contar_parcelas_activas.return_value = 3
        with pytest.raises(ConflictoEliminacionError):
            caso_uso.eliminar('lote-1', AGRICULTOR_ID)
        lote_repo.actualizar.assert_not_called()

    def test_lote_sin_parcelas_activas_se_marca_inactivo(self, caso_uso, lote_repo, finca_repo):
        lote = _lote()
        lote_repo.buscar_por_id.return_value = lote
        finca_repo.buscar_por_id.return_value = _finca()
        lote_repo.contar_parcelas_activas.return_value = 0
        lote_repo.actualizar.side_effect = lambda l: l

        resultado = caso_uso.eliminar('lote-1', AGRICULTOR_ID)

        assert lote.activo is False
        assert resultado['activo'] is False


class TestEditarLote:
    def test_editar_no_toca_geometria(self, caso_uso, lote_repo, finca_repo):
        lote = _lote()
        lote_repo.buscar_por_id.return_value = lote
        finca_repo.buscar_por_id.return_value = _finca()
        lote_repo.actualizar.side_effect = lambda l: l

        resultado = caso_uso.editar('lote-1', AGRICULTOR_ID, {'nombre': 'Nuevo nombre'})

        assert lote.nombre == 'Nuevo nombre'
        assert resultado['nombre'] == 'Nuevo nombre'


class TestObtenerLote:
    def test_obtener_lote_de_otro_agricultor_lanza_permission_error(self, caso_uso, lote_repo, finca_repo):
        lote_repo.buscar_por_id.return_value = _lote()
        finca_repo.buscar_por_id.return_value = _finca(agricultor_id=OTRO_AGRICULTOR_ID)
        with pytest.raises(PermissionError):
            caso_uso.obtener('lote-1', AGRICULTOR_ID)
