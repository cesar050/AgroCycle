"""
Tests unitarios — CalcularKsSueloUseCase
Valida el coeficiente de estres hidrico bidireccional
Ks_final = min(Ks_deficit, Ks_exceso).
"""
import pytest
from app.application.use_cases.mapa.calcular_ks_suelo import CalcularKsSueloUseCase


@pytest.fixture
def caso_uso():
    return CalcularKsSueloUseCase()


class TestKsDeficit:
    def test_humedad_en_punto_de_marchitez_es_ks_cero(self, caso_uso):
        r = caso_uso.calcular(0.14, tipo_suelo_id=6)
        assert r['ks_deficit'] == 0.0

    def test_humedad_por_debajo_de_marchitez_sigue_en_cero(self, caso_uso):
        r = caso_uso.calcular(0.05, tipo_suelo_id=6)
        assert r['ks_deficit'] == 0.0

    def test_humedad_en_capacidad_de_campo_es_ks_uno(self, caso_uso):
        r = caso_uso.calcular(0.34, tipo_suelo_id=6)
        assert r['ks_deficit'] == 1.0

    def test_humedad_intermedia_da_ks_entre_cero_y_uno(self, caso_uso):
        r = caso_uso.calcular(0.20, tipo_suelo_id=6)
        assert 0.0 < r['ks_deficit'] < 1.0


class TestKsExceso:
    def test_humedad_en_capacidad_de_campo_es_sin_exceso(self, caso_uso):
        r = caso_uso.calcular(0.34, tipo_suelo_id=6)
        assert r['ks_exceso'] == 1.0

    def test_humedad_en_saturacion_es_ks_exceso_cero(self, caso_uso):
        r = caso_uso.calcular(0.44, tipo_suelo_id=6)
        assert r['ks_exceso'] == 0.0

    def test_humedad_por_encima_de_saturacion_sigue_en_cero(self, caso_uso):
        r = caso_uso.calcular(0.60, tipo_suelo_id=6)
        assert r['ks_exceso'] == 0.0

    def test_humedad_entre_capacidad_y_saturacion_da_ks_entre_cero_y_uno(self, caso_uso):
        r = caso_uso.calcular(0.40, tipo_suelo_id=6)
        assert 0.0 < r['ks_exceso'] < 1.0


class TestKsFinalBidireccional:
    def test_ks_final_es_el_minimo_de_ambos_en_deficit(self, caso_uso):
        r = caso_uso.calcular(0.05, tipo_suelo_id=6)
        assert r['ks_final'] == min(r['ks_deficit'], r['ks_exceso'])
        assert r['ks_final'] == r['ks_deficit']

    def test_ks_final_es_el_minimo_de_ambos_en_exceso(self, caso_uso):
        r = caso_uso.calcular(0.60, tipo_suelo_id=6)
        assert r['ks_final'] == min(r['ks_deficit'], r['ks_exceso'])
        assert r['ks_final'] == r['ks_exceso']

    def test_rango_optimo_sin_estres(self, caso_uso):
        r = caso_uso.calcular(0.34, tipo_suelo_id=6)
        assert r['ks_final'] == 1.0
        assert r['nivel_estres'] == 'sin_estres'

    def test_clasificacion_estres_por_deficit_severo(self, caso_uso):
        r = caso_uso.calcular(0.05, tipo_suelo_id=6)
        assert r['nivel_estres'] == 'estres_deficit_severo'

    def test_clasificacion_estres_por_exceso_severo(self, caso_uso):
        r = caso_uso.calcular(0.60, tipo_suelo_id=6)
        assert r['nivel_estres'] == 'estres_exceso_severo'

    def test_tipo_suelo_desconocido_usa_valores_por_defecto(self, caso_uso):
        r = caso_uso.calcular(0.20, tipo_suelo_id=999)
        r_defecto = caso_uso.calcular(0.20, tipo_suelo_id=6)
        assert r == r_defecto

    def test_tipo_suelo_none_usa_valores_por_defecto(self, caso_uso):
        r = caso_uso.calcular(0.20, tipo_suelo_id=None)
        r_defecto = caso_uso.calcular(0.20, tipo_suelo_id=6)
        assert r == r_defecto
