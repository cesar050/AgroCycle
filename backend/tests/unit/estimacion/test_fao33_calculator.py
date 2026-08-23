"""
Tests unitarios — FAO33Calculator
Valida el modelo FAO-33 (Stewart, 1977):
    Ya = Ym * (1 - Ky * (1 - Ks))
"""
import pytest
from unittest.mock import MagicMock, patch
from app.infrastructure.ml.fao33_calculator import FAO33Calculator, KY_MAIZ


@pytest.fixture
def db_mock():
    return MagicMock()


@pytest.fixture
def calculador(db_mock):
    return FAO33Calculator(db=db_mock)


@pytest.fixture
def datos_etapas_sin_estres():
    return [
        {'etapa': 'emergencia', 'dias_con_datos': 7, 'ks_promedio': 1.0, 'precip_total': 25.0, 'temp_promedio': 22.0},
        {'etapa': 'crecimiento_vegetativo', 'dias_con_datos': 30, 'ks_promedio': 1.0, 'precip_total': 80.0, 'temp_promedio': 24.0},
        {'etapa': 'floracion', 'dias_con_datos': 25, 'ks_promedio': 1.0, 'precip_total': 60.0, 'temp_promedio': 25.0},
        {'etapa': 'llenado_grano', 'dias_con_datos': 30, 'ks_promedio': 1.0, 'precip_total': 50.0, 'temp_promedio': 23.0},
        {'etapa': 'maduracion', 'dias_con_datos': 20, 'ks_promedio': 1.0, 'precip_total': 10.0, 'temp_promedio': 26.0},
    ]


@pytest.fixture
def datos_etapas_con_estres_floracion():
    return [
        {'etapa': 'emergencia', 'dias_con_datos': 7, 'ks_promedio': 1.0, 'precip_total': 25.0, 'temp_promedio': 22.0},
        {'etapa': 'crecimiento_vegetativo', 'dias_con_datos': 30, 'ks_promedio': 0.90, 'precip_total': 40.0, 'temp_promedio': 24.0},
        {'etapa': 'floracion', 'dias_con_datos': 25, 'ks_promedio': 0.40, 'precip_total': 5.0, 'temp_promedio': 30.0},
        {'etapa': 'llenado_grano', 'dias_con_datos': 30, 'ks_promedio': 0.60, 'precip_total': 20.0, 'temp_promedio': 28.0},
        {'etapa': 'maduracion', 'dias_con_datos': 20, 'ks_promedio': 0.80, 'precip_total': 8.0, 'temp_promedio': 27.0},
    ]


class TestCoeficientesKy:
    def test_ky_floracion_es_el_mas_alto(self):
        assert KY_MAIZ['floracion'] == 1.50

    def test_ky_emergencia(self):
        assert KY_MAIZ['emergencia'] == 0.20

    def test_ky_crecimiento_vegetativo(self):
        assert KY_MAIZ['crecimiento_vegetativo'] == 0.40

    def test_ky_llenado_grano(self):
        assert KY_MAIZ['llenado_grano'] == 0.50

    def test_ky_maduracion(self):
        assert KY_MAIZ['maduracion'] == 0.20

    def test_ky_pre_siembra_es_cero(self):
        assert KY_MAIZ['pre_siembra'] == 0.00

    def test_ky_cosecha_es_cero(self):
        assert KY_MAIZ['cosecha'] == 0.00

    def test_todos_ky_son_no_negativos(self):
        for etapa, ky in KY_MAIZ.items():
            assert ky >= 0.0


class TestFactorPendiente:
    def test_sin_pendiente_factor_es_uno(self, calculador):
        assert calculador._factor_pendiente(None) == 1.00

    def test_pendiente_cero_factor_es_uno(self, calculador):
        assert calculador._factor_pendiente(0) == 1.00

    def test_pendiente_menor_5_factor_es_uno(self, calculador):
        assert calculador._factor_pendiente(4.9) == 1.00

    def test_parcela_choza_pendiente_10_factor_097(self, calculador):
        assert calculador._factor_pendiente(10.17) == 0.97

    def test_pendiente_entre_15_y_25_factor_093(self, calculador):
        assert calculador._factor_pendiente(20.0) == 0.93

    def test_pendiente_mayor_25_factor_088(self, calculador):
        assert calculador._factor_pendiente(30.0) == 0.88

    def test_pendiente_exactamente_15_factor_093(self, calculador):
        assert calculador._factor_pendiente(15.0) == 0.93

    def test_pendiente_exactamente_25_factor_088(self, calculador):
        assert calculador._factor_pendiente(25.0) == 0.88


class TestMargenError:
    def test_sin_datos_margen_maximo(self, calculador):
        assert calculador._margen_error(0, 120) == 35.0

    def test_ciclo_completo_margen_minimo(self, calculador):
        assert calculador._margen_error(120, 120) == 8.0

    def test_cobertura_media_margen_intermedio(self, calculador):
        margen = calculador._margen_error(60, 120)
        assert 8.0 < margen < 35.0

    def test_margen_nunca_baja_de_8(self, calculador):
        assert calculador._margen_error(200, 120) == 8.0

    def test_margen_disminuye_con_mas_datos(self, calculador):
        m30 = calculador._margen_error(30, 120)
        m60 = calculador._margen_error(60, 120)
        m90 = calculador._margen_error(90, 120)
        assert m30 > m60 > m90


class TestKsPonderado:
    def test_ks_uno_cuando_no_hay_etapas_con_ky(self, calculador):
        datos = [
            {'etapa': 'pre_siembra', 'ks_promedio': 0.5, 'dias_con_datos': 5},
            {'etapa': 'cosecha', 'ks_promedio': 0.5, 'dias_con_datos': 5},
        ]
        assert calculador._ks_ponderado(datos) == 1.0

    def test_ks_ponderado_sin_estres(self, calculador, datos_etapas_sin_estres):
        assert calculador._ks_ponderado(datos_etapas_sin_estres) == 1.0

    def test_estres_total_en_floracion_domina_ponderado(self, calculador):
        """
        Floracion Ky=1.50 con Ks=0 y llenado_grano Ky=0.50 con Ks=1.0.
        El Ks ponderado debe ser menor que 0.5 porque floracion pesa mas.
        """
        datos = [
            {'etapa': 'floracion', 'ks_promedio': 0.0, 'dias_con_datos': 20},
            {'etapa': 'llenado_grano', 'ks_promedio': 1.0, 'dias_con_datos': 20},
        ]
        ks = calculador._ks_ponderado(datos)
        # Ks ponderado = (0.0*1.5 + 1.0*0.5) / (1.5 + 0.5) = 0.5/2.0 = 0.25
        assert ks == pytest.approx(0.25, abs=0.01)

    def test_ks_nunca_supera_uno(self, calculador, datos_etapas_sin_estres):
        assert calculador._ks_ponderado(datos_etapas_sin_estres) <= 1.0

    def test_ks_nunca_es_negativo(self, calculador, datos_etapas_con_estres_floracion):
        assert calculador._ks_ponderado(datos_etapas_con_estres_floracion) >= 0.0


class TestCalcularReduccion:
    def test_sin_estres_reduccion_es_cero(self, calculador, datos_etapas_sin_estres):
        reduccion, _, _ = calculador._calcular_reduccion(datos_etapas_sin_estres, 100.0)
        assert reduccion == 0.0

    def test_estres_severo_en_floracion_genera_reduccion_alta(
        self, calculador, datos_etapas_con_estres_floracion
    ):
        reduccion, _, _ = calculador._calcular_reduccion(datos_etapas_con_estres_floracion, 100.0)
        assert reduccion > 50.0

    def test_factores_negativos_con_ks_bajo(self, calculador, datos_etapas_con_estres_floracion):
        _, factores, _ = calculador._calcular_reduccion(datos_etapas_con_estres_floracion, 100.0)
        etapas = [f['etapa'] for f in factores['negativos']]
        assert 'floracion' in etapas

    def test_factores_positivos_con_ks_optimo(self, calculador, datos_etapas_sin_estres):
        _, factores, _ = calculador._calcular_reduccion(datos_etapas_sin_estres, 100.0)
        assert len(factores['positivos']) > 0

    def test_fao33_permite_reduccion_mayor_al_potencial_con_ky_alto(self, calculador):
        """
        FAO-33 con Ky=1.50 y Ks=0 en floracion:
        reduccion = 100 * 1.50 * (1 - 0) = 150 qq/ha
        Esto es matematicamente correcto segun FAO-33.
        El codigo protege la produccion final con max(..., 0) no la reduccion.
        """
        datos = [{'etapa': 'floracion', 'dias_con_datos': 25, 'ks_promedio': 0.0,
                  'precip_total': 0.0, 'temp_promedio': 35.0}]
        reduccion, _, _ = calculador._calcular_reduccion(datos, 100.0)
        assert reduccion == pytest.approx(150.0, abs=0.1)

    def test_produccion_final_nunca_es_negativa(self, calculador):
        """
        Aunque la reduccion supere el potencial, la produccion
        final debe ser cero, no negativa. El max() del codigo garantiza esto.
        """
        datos = [{'etapa': 'floracion', 'dias_con_datos': 25, 'ks_promedio': 0.0,
                  'precip_total': 0.0, 'temp_promedio': 35.0}]
        with patch.object(calculador, '_datos_por_etapa', return_value=datos):
            resultado = calculador.calcular(
                temporada_parcela_id='uuid-test',
                produccion_potencial_qq_ha=100.0,
                ciclo_vegetativo_dias=120,
                superficie_ha=1.0,
            )
        assert resultado['valor_qq_ha'] >= 0.0


class TestEstimacionSinDatos:
    def test_produccion_es_70_porciento_del_potencial(self, calculador):
        resultado = calculador._estimacion_sin_datos(100.0, 1.0)
        assert resultado['valor_qq_ha'] == 70.0

    def test_margen_error_maximo_sin_datos(self, calculador):
        resultado = calculador._estimacion_sin_datos(100.0, 1.0)
        assert resultado['margen_error_porcentaje'] == 35.0

    def test_produccion_total_considera_superficie(self, calculador):
        resultado = calculador._estimacion_sin_datos(100.0, 0.6754)
        assert resultado['valor_total_qq'] == round(70.0 * 0.6754, 2)

    def test_hay_al_menos_un_factor_negativo(self, calculador):
        resultado = calculador._estimacion_sin_datos(100.0, 1.0)
        assert len(resultado['factores_negativos']) > 0

    def test_no_hay_factores_positivos_sin_datos(self, calculador):
        resultado = calculador._estimacion_sin_datos(100.0, 1.0)
        assert resultado['factores_positivos'] == []


class TestCalcularIntegracion:
    def test_calcular_sin_datos_db_retorna_estimacion_base(self, calculador):
        with patch.object(calculador, '_datos_por_etapa', return_value=[]):
            resultado = calculador.calcular(
                temporada_parcela_id='uuid-test',
                produccion_potencial_qq_ha=80.0,
                ciclo_vegetativo_dias=120,
                superficie_ha=0.6754,
            )
        assert resultado['valor_qq_ha'] == round(80.0 * 0.70, 2)
        assert resultado['margen_error_porcentaje'] == 35.0

    def test_calcular_sin_estres_retorna_casi_el_potencial(
        self, calculador, datos_etapas_sin_estres
    ):
        with patch.object(calculador, '_datos_por_etapa', return_value=datos_etapas_sin_estres):
            resultado = calculador.calcular(
                temporada_parcela_id='uuid-test',
                produccion_potencial_qq_ha=80.0,
                ciclo_vegetativo_dias=120,
                superficie_ha=0.6754,
                pendiente_porcentaje=10.17,
            )
        assert resultado['valor_qq_ha'] == round(80.0 * 0.97, 2)

    def test_calcular_con_estres_severo_reduce_rendimiento(
        self, calculador, datos_etapas_con_estres_floracion
    ):
        with patch.object(calculador, '_datos_por_etapa', return_value=datos_etapas_con_estres_floracion):
            resultado = calculador.calcular(
                temporada_parcela_id='uuid-test',
                produccion_potencial_qq_ha=80.0,
                ciclo_vegetativo_dias=120,
                superficie_ha=0.6754,
            )
        assert resultado['valor_qq_ha'] < 80.0 * 0.70

    def test_resultado_tiene_estructura_completa(
        self, calculador, datos_etapas_sin_estres
    ):
        with patch.object(calculador, '_datos_por_etapa', return_value=datos_etapas_sin_estres):
            resultado = calculador.calcular(
                temporada_parcela_id='uuid-test',
                produccion_potencial_qq_ha=80.0,
                ciclo_vegetativo_dias=120,
                superficie_ha=1.0,
            )
        for campo in ['valor_qq_ha', 'valor_total_qq', 'margen_error_porcentaje',
                      'etapas_detalle', 'factores_positivos', 'factores_negativos',
                      'variables_entrada']:
            assert campo in resultado

    def test_produccion_nunca_es_negativa(
        self, calculador, datos_etapas_con_estres_floracion
    ):
        with patch.object(calculador, '_datos_por_etapa', return_value=datos_etapas_con_estres_floracion):
            resultado = calculador.calcular(
                temporada_parcela_id='uuid-test',
                produccion_potencial_qq_ha=80.0,
                ciclo_vegetativo_dias=120,
                superficie_ha=0.6754,
            )
        assert resultado['valor_qq_ha'] >= 0.0
        assert resultado['valor_total_qq'] >= 0.0

    def test_caso_real_parcela_choza(self, calculador):
        """
        Caso real: Parcela Choza, Finca Ramos, Bramaderos.
        Superficie: 0.6754 ha, Pendiente: 10.17%, Potencial: 80 qq/ha.
        Produccion real registrada: 48.5 qq totales = 71.81 qq/ha.
        Con buenas condiciones hidricas el modelo debe acercarse al real.
        """
        datos_buenas_condiciones = [
            {'etapa': 'emergencia', 'dias_con_datos': 6,
             'ks_promedio': 1.0, 'precip_total': 18.0, 'temp_promedio': 21.0},
            {'etapa': 'crecimiento_vegetativo', 'dias_con_datos': 30,
             'ks_promedio': 1.0, 'precip_total': 65.0, 'temp_promedio': 24.0},
            {'etapa': 'floracion', 'dias_con_datos': 25,
             'ks_promedio': 0.95, 'precip_total': 45.0, 'temp_promedio': 25.0},
            {'etapa': 'llenado_grano', 'dias_con_datos': 28,
             'ks_promedio': 0.90, 'precip_total': 30.0, 'temp_promedio': 26.0},
            {'etapa': 'maduracion', 'dias_con_datos': 18,
             'ks_promedio': 0.95, 'precip_total': 8.0, 'temp_promedio': 27.0},
        ]
        with patch.object(calculador, '_datos_por_etapa', return_value=datos_buenas_condiciones):
            resultado = calculador.calcular(
                temporada_parcela_id='299dde6c-d5ec-4899-81bd-0da9252b0e4a',
                produccion_potencial_qq_ha=80.0,
                ciclo_vegetativo_dias=120,
                superficie_ha=0.6754,
                pendiente_porcentaje=10.17,
            )
        # Con condiciones hidricas buenas la estimacion debe ser mayor a 60 qq/ha
        assert resultado['valor_qq_ha'] > 60.0
        # Y no superar el potencial ajustado por pendiente
        assert resultado['valor_qq_ha'] <= 80.0 * 0.97
