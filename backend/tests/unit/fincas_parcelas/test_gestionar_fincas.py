"""
Tests unitarios — GestionarFincasUseCase.eliminar
Valida el bloqueo de borrado cuando hay lotes activos (409) y el
soft-delete cuando la finca ya no tiene hijos.
"""
import pytest
from unittest.mock import MagicMock
from app.application.use_cases.fincas_parcelas.gestionar_fincas import GestionarFincasUseCase
from app.domain.entities.finca import Finca
from app.domain.exceptions import ConflictoEliminacionError

AGRICULTOR_ID = 'agricultor-1'
OTRO_AGRICULTOR_ID = 'agricultor-2'


@pytest.fixture
def finca_repo():
    return MagicMock()


@pytest.fixture
def caso_uso(finca_repo):
    return GestionarFincasUseCase(finca_repo)


def _finca(agricultor_id=AGRICULTOR_ID):
    return Finca(agricultor_id=agricultor_id, nombre='Finca Test', id='finca-1')


class TestEliminarFinca:
    def test_finca_no_encontrada_lanza_value_error(self, caso_uso, finca_repo):
        finca_repo.buscar_por_id.return_value = None
        with pytest.raises(ValueError):
            caso_uso.eliminar('finca-1', AGRICULTOR_ID)

    def test_finca_de_otro_agricultor_lanza_permission_error(self, caso_uso, finca_repo):
        finca_repo.buscar_por_id.return_value = _finca(agricultor_id=OTRO_AGRICULTOR_ID)
        with pytest.raises(PermissionError):
            caso_uso.eliminar('finca-1', AGRICULTOR_ID)

    def test_finca_con_lotes_activos_lanza_conflicto(self, caso_uso, finca_repo):
        finca_repo.buscar_por_id.return_value = _finca()
        finca_repo.contar_lotes_activos.return_value = 2
        with pytest.raises(ConflictoEliminacionError):
            caso_uso.eliminar('finca-1', AGRICULTOR_ID)
        finca_repo.actualizar.assert_not_called()

    def test_finca_sin_lotes_activos_se_marca_inactiva(self, caso_uso, finca_repo):
        finca = _finca()
        finca_repo.buscar_por_id.return_value = finca
        finca_repo.contar_lotes_activos.return_value = 0
        finca_repo.actualizar.side_effect = lambda f: f

        resultado = caso_uso.eliminar('finca-1', AGRICULTOR_ID)

        assert finca.activo is False
        finca_repo.actualizar.assert_called_once_with(finca)
        assert resultado['activo'] is False
