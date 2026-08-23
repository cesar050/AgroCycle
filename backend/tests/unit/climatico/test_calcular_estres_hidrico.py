"""
Tests unitarios — CalcularEstresHidricoUseCase
Valida el calculo del coeficiente de estres hidrico Ks segun FAO-56.
"""
import pytest
from unittest.mock import MagicMock
from app.application.use_cases.climatico.calcular_estres_hidrico import (
    CalcularEstresHidricoUseCase
)


@pytest.fixture
def db_mock():
    return MagicMock()


@pytest.fixture
def caso_uso(db_mock):
    return CalcularEstresHidricoUseCase(db=db_mock)


class TestClasificarEstres:
    def test_ks_uno_es_sin_estres(self, caso_uso):
        assert caso_uso._clasificar_estres(1.0) == 'sin_estres'

    def test_ks_mayor_a_uno_es_sin_estres(self, caso_uso):
        assert caso_uso._clasificar_estres(1.5) == 'sin_estres'

    def test_ks_075_es_estres_leve(self, caso_uso):
        assert caso_uso._clasificar_estres(0.75) == 'estres_leve'

    def test_ks_080_es_estres_leve(self, caso_uso):
        assert caso_uso._clasificar_estres(0.80) == 'estres_leve'

    def test_ks_050_es_estres_moderado(self, caso_uso):
        assert caso_uso._clasificar_estres(0.50) == 'estres_moderado'

    def test_ks_060_es_estres_moderado(self, caso_uso):
        assert caso_uso._clasificar_estres(0.60) == 'estres_moderado'

    def test_ks_049_es_estres_severo(self, caso_uso):
        assert caso_uso._clasificar_estres(0.49) == 'estres_severo'

    def test_ks_cero_es_estres_severo(self, caso_uso):
        assert caso_uso._clasificar_estres(0.0) == 'estres_severo'

    def test_limite_leve_moderado(self, caso_uso):
        assert caso_uso._clasificar_estres(0.74) == 'estres_moderado'
        assert caso_uso._clasificar_estres(0.75) == 'estres_leve'

    def test_limite_moderado_severo(self, caso_uso):
        assert caso_uso._clasificar_estres(0.50) == 'estres_moderado'
        assert caso_uso._clasificar_estres(0.49) == 'estres_severo'


class TestCalcularKsYHumedad:
    def test_sin_etc_ni_precipitacion_humedad_no_cambia(self, caso_uso):
        ks, humedad = caso_uso._calcular_ks_y_humedad(
            humedad_anterior=70.0, precipitacion=0.0, etc=0.0,
            capacidad_campo_mm=100.0, factor_escurrimiento=0.0
        )
        assert humedad == 70.0
        assert ks == 1.0

    def test_lluvia_aumenta_humedad(self, caso_uso):
        _, humedad_sin = caso_uso._calcular_ks_y_humedad(
            humedad_anterior=50.0, precipitacion=0.0, etc=0.0,
            capacidad_campo_mm=100.0, factor_escurrimiento=0.0
        )
        _, humedad_con = caso_uso._calcular_ks_y_humedad(
            humedad_anterior=50.0, precipitacion=20.0, etc=0.0,
            capacidad_campo_mm=100.0, factor_escurrimiento=0.0
        )
        assert humedad_con > humedad_sin

    def test_evapotranspiracion_reduce_humedad(self, caso_uso):
        _, humedad_sin = caso_uso._calcular_ks_y_humedad(
            humedad_anterior=70.0, precipitacion=0.0, etc=0.0,
            capacidad_campo_mm=100.0, factor_escurrimiento=0.0
        )
        _, humedad_con = caso_uso._calcular_ks_y_humedad(
            humedad_anterior=70.0, precipitacion=0.0, etc=5.0,
            capacidad_campo_mm=100.0, factor_escurrimiento=0.0
        )
        assert humedad_con < humedad_sin

    def test_humedad_no_supera_capacidad_campo(self, caso_uso):
        _, humedad = caso_uso._calcular_ks_y_humedad(
            humedad_anterior=90.0, precipitacion=100.0, etc=0.0,
            capacidad_campo_mm=100.0, factor_escurrimiento=0.0
        )
        assert humedad <= 100.0

    def test_humedad_no_baja_de_cero(self, caso_uso):
        _, humedad = caso_uso._calcular_ks_y_humedad(
            humedad_anterior=5.0, precipitacion=0.0, etc=50.0,
            capacidad_campo_mm=100.0, factor_escurrimiento=0.0
        )
        assert humedad >= 0.0

    def test_ks_es_uno_con_humedad_alta(self, caso_uso):
        ks, _ = caso_uso._calcular_ks_y_humedad(
            humedad_anterior=80.0, precipitacion=0.0, etc=2.0,
            capacidad_campo_mm=100.0, factor_escurrimiento=0.0
        )
        assert ks == 1.0

    def test_ks_menor_uno_con_humedad_baja(self, caso_uso):
        ks, _ = caso_uso._calcular_ks_y_humedad(
            humedad_anterior=20.0, precipitacion=0.0, etc=5.0,
            capacidad_campo_mm=100.0, factor_escurrimiento=0.0
        )
        assert ks < 1.0

    def test_capacidad_campo_cero_retorna_humedad_anterior(self, caso_uso):
        ks, humedad = caso_uso._calcular_ks_y_humedad(
            humedad_anterior=70.0, precipitacion=10.0, etc=3.0,
            capacidad_campo_mm=0.0, factor_escurrimiento=0.0
        )
        assert humedad == 70.0
        assert ks == 1.0

    def test_pendiente_alta_reduce_precipitacion_efectiva(self, caso_uso):
        _, humedad_sin = caso_uso._calcular_ks_y_humedad(
            humedad_anterior=50.0, precipitacion=20.0, etc=0.0,
            capacidad_campo_mm=100.0, factor_escurrimiento=0.0
        )
        _, humedad_con = caso_uso._calcular_ks_y_humedad(
            humedad_anterior=50.0, precipitacion=20.0, etc=0.0,
            capacidad_campo_mm=100.0, factor_escurrimiento=0.35
        )
        assert humedad_sin > humedad_con


class TestCalcularEstado:
    """
    NOTA: Los limites de etapa se calculan como porcentaje del ciclo.
    porcentaje = (dias / ciclo) * 100
    Los dias de prueba deben estar CLARAMENTE dentro de cada rango,
    no en los limites exactos para evitar ambiguedades de borde.
    Rangos reales del codigo:
    < 5%  → emergencia
    < 30% → crecimiento_vegetativo
    < 55% → floracion
    < 80% → llenado_grano
    < 95% → maduracion
    >= 95% → cosecha
    """

    def test_antes_de_siembra_es_pre_siembra(self, caso_uso):
        from datetime import date
        assert caso_uso._calcular_estado(
            date(2027, 1, 15), date(2027, 1, 10), 120
        ) == 'pre_siembra'

    def test_primer_dia_es_emergencia(self, caso_uso):
        from datetime import date
        assert caso_uso._calcular_estado(
            date(2027, 1, 15), date(2027, 1, 15), 120
        ) == 'emergencia'

    def test_dia_20_es_crecimiento_vegetativo(self, caso_uso):
        """Dia 20 = 16.7% del ciclo — claramente en crecimiento vegetativo."""
        from datetime import date, timedelta
        siembra = date(2027, 1, 15)
        fecha = siembra + timedelta(days=20)
        assert caso_uso._calcular_estado(siembra, fecha, 120) == 'crecimiento_vegetativo'

    def test_dia_50_es_floracion(self, caso_uso):
        """Dia 50 = 41.7% del ciclo — claramente en floracion."""
        from datetime import date, timedelta
        siembra = date(2027, 1, 15)
        fecha = siembra + timedelta(days=50)
        assert caso_uso._calcular_estado(siembra, fecha, 120) == 'floracion'

    def test_dia_80_es_llenado_grano(self, caso_uso):
        """Dia 80 = 66.7% del ciclo — claramente en llenado de grano."""
        from datetime import date, timedelta
        siembra = date(2027, 1, 15)
        fecha = siembra + timedelta(days=80)
        assert caso_uso._calcular_estado(siembra, fecha, 120) == 'llenado_grano'

    def test_dia_110_es_maduracion(self, caso_uso):
        """Dia 110 = 91.7% del ciclo — claramente en maduracion."""
        from datetime import date, timedelta
        siembra = date(2027, 1, 15)
        fecha = siembra + timedelta(days=110)
        assert caso_uso._calcular_estado(siembra, fecha, 120) == 'maduracion'

    def test_dia_120_es_cosecha(self, caso_uso):
        """Dia 120 = 100% — cosecha."""
        from datetime import date, timedelta
        siembra = date(2027, 1, 15)
        fecha = siembra + timedelta(days=120)
        assert caso_uso._calcular_estado(siembra, fecha, 120) == 'cosecha'

    def test_sin_fecha_siembra_es_pre_siembra(self, caso_uso):
        from datetime import date
        assert caso_uso._calcular_estado(None, date(2027, 1, 15), 120) == 'pre_siembra'

    def test_sin_ciclo_es_pre_siembra(self, caso_uso):
        from datetime import date
        assert caso_uso._calcular_estado(date(2027, 1, 15), date(2027, 2, 1), None) == 'pre_siembra'


class TestInterpretarKs:
    def test_ks_excelente(self, caso_uso):
        assert 'excelente' in caso_uso._interpretar_ks(0.97).lower()

    def test_ks_leve(self, caso_uso):
        assert 'leve' in caso_uso._interpretar_ks(0.85).lower()

    def test_ks_moderado(self, caso_uso):
        assert 'moderado' in caso_uso._interpretar_ks(0.70).lower()

    def test_ks_severo(self, caso_uso):
        assert 'severo' in caso_uso._interpretar_ks(0.50).lower()

    def test_interpretacion_nunca_es_vacia(self, caso_uso):
        for ks in [0.0, 0.3, 0.5, 0.7, 0.8, 0.95, 1.0]:
            assert len(caso_uso._interpretar_ks(ks)) > 0
