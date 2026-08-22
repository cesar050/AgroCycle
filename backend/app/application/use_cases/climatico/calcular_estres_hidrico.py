"""
Caso de uso: CU-CLI-007 Calcular Indice de Estres Hidrico.
Calcula el factor Ks (coeficiente de estres hidrico) segun FAO-56
y persiste los resultados en indicadores_estres_hidrico para que
el modulo de estimacion FAO-33 pueda leerlos sin recalcular.
"""
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.infrastructure.logging.logger import configurar_logger, log_caso_de_uso

logger = configurar_logger('estres_hidrico')


class CalcularEstresHidricoUseCase:
    """
    Implementa CU-CLI-007.

    Responsabilidades:
    1. Calcular Ks diario usando balance hidrico FAO-56
    2. Persistir resultados en indicadores_estres_hidrico
    3. Retornar resumen del periodo para el agricultor

    El modulo de estimacion (FAO-33) lee de indicadores_estres_hidrico.
    Este caso de uso debe ejecutarse antes de generar estimaciones.
    """

    FRACCION_AGUA_DISPONIBLE = 0.55

    AGUA_DISPONIBLE_SUELO = {
        1: 120,
        2: 220,
        3: 180,
        4: 280,
        5: 80,
        6: 200,
    }

    PROFUNDIDAD_RADICULAR = {
        'pre_siembra':            0.0,
        'emergencia':             0.15,
        'crecimiento_vegetativo': 0.50,
        'floracion':              0.80,
        'llenado_grano':          0.80,
        'maduracion':             0.70,
        'cosecha':                0.50,
        'post_cosecha':           0.30,
    }

    def __init__(self, db: Session):
        self.db = db

    @log_caso_de_uso('calcular_estres_hidrico')
    def ejecutar(
        self,
        temporada_parcela_id: str,
        parcela_id: str,
        fecha_inicio: date,
        fecha_fin: date
    ) -> dict:
        """
        Calcula y persiste el estres hidrico para un periodo.
        Retorna resumen con Ks promedio e impacto en rendimiento.
        """
        tp_data = self._obtener_datos_temporada(
            temporada_parcela_id, parcela_id
        )
        datos_climaticos = self._obtener_datos_climaticos(
            parcela_id, fecha_inicio, fecha_fin
        )

        resultados = self._calcular_ks_diario(tp_data, datos_climaticos)

        # Persistir para que FAO-33 pueda leerlos
        self._persistir_indicadores(temporada_parcela_id, resultados)

        return self._construir_resumen(
            temporada_parcela_id, fecha_inicio, fecha_fin, resultados
        )

    # ------------------------------------------------------------------
    # Métodos privados de obtención de datos
    # ------------------------------------------------------------------

    def _obtener_datos_temporada(
        self, temporada_parcela_id: str, parcela_id: str
    ):
        tp_data = self.db.execute(
            text("""
                SELECT
                    tp.estado_fenologico,
                    tp.fecha_siembra,
                    vs.ciclo_vegetativo_dias,
                    vs.kc_emergencia,
                    vs.kc_crecimiento,
                    vs.kc_floracion,
                    vs.kc_llenado_grano,
                    vs.kc_maduracion,
                    p.tipo_suelo_id,
                    p.pendiente_porcentaje
                FROM temporada_parcelas tp
                LEFT JOIN variedades_semilla vs
                    ON tp.variedad_semilla_id = vs.id
                LEFT JOIN parcelas p
                    ON tp.parcela_id = CAST(:parcela_id AS uuid)
                WHERE tp.id = CAST(:tp_id AS uuid)
            """),
            {
                'tp_id': temporada_parcela_id,
                'parcela_id': parcela_id
            }
        ).fetchone()

        if not tp_data:
            raise ValueError("TemporadaParcela no encontrada")

        return tp_data

    def _obtener_datos_climaticos(
        self, parcela_id: str, fecha_inicio: date, fecha_fin: date
    ):
        datos = self.db.execute(
            text("""
                SELECT fecha, precipitacion_mm, evapotranspiracion_mm
                FROM datos_climaticos
                WHERE parcela_id = CAST(:parcela_id AS uuid)
                  AND fecha BETWEEN :inicio AND :fin
                ORDER BY fecha ASC
            """),
            {
                'parcela_id': parcela_id,
                'inicio': fecha_inicio,
                'fin': fecha_fin
            }
        ).fetchall()

        if not datos:
            raise ValueError("No hay datos climaticos para el periodo")

        return datos

    # ------------------------------------------------------------------
    # Métodos privados de cálculo
    # ------------------------------------------------------------------

    def _calcular_ks_diario(self, tp_data, datos_climaticos) -> list:
        """
        Itera día a día calculando el balance hídrico y el Ks FAO-56.
        La humedad del día anterior alimenta el cálculo del día siguiente.
        """
        tipo_suelo = tp_data.tipo_suelo_id or 6
        agua_disponible_mm_m = float(
            self.AGUA_DISPONIBLE_SUELO.get(tipo_suelo, 200)
        )
        pendiente = float(tp_data.pendiente_porcentaje or 0)
        factor_escurrimiento = min(pendiente / 100 * 0.5, 0.4)

        resultados = []
        humedad_anterior = 70.0

        for dato in datos_climaticos:
            fecha = dato.fecha
            precipitacion = float(dato.precipitacion_mm or 0)
            et0 = float(dato.evapotranspiracion_mm or 0)

            estado = self._calcular_estado(
                tp_data.fecha_siembra, fecha,
                tp_data.ciclo_vegetativo_dias
            )
            kc = self._obtener_kc(estado, tp_data)
            etc = round(et0 * kc, 2)

            prof_radicular = self.PROFUNDIDAD_RADICULAR.get(estado, 0.5)
            capacidad_campo_mm = agua_disponible_mm_m * prof_radicular

            ks, humedad_porcentaje = self._calcular_ks_y_humedad(
                humedad_anterior, precipitacion, etc,
                capacidad_campo_mm, factor_escurrimiento
            )

            resultados.append({
                'fecha': str(fecha),
                'estado_fenologico': estado,
                'humedad_porcentaje': humedad_porcentaje,
                'ks': ks,
                'nivel_estres': self._clasificar_estres(ks),
                'etc_mm': etc,
                'et0_mm': round(et0, 2),
            })

            humedad_anterior = humedad_porcentaje

        return resultados

    def _calcular_ks_y_humedad(
        self,
        humedad_anterior: float,
        precipitacion: float,
        etc: float,
        capacidad_campo_mm: float,
        factor_escurrimiento: float
    ) -> tuple:
        """
        Calcula Ks y humedad resultante para un día.
        Retorna (ks, humedad_porcentaje).
        """
        if capacidad_campo_mm == 0:
            return 1.0, humedad_anterior

        agua_actual = (humedad_anterior / 100) * capacidad_campo_mm
        agua_actual += precipitacion * (1 - factor_escurrimiento)
        agua_actual -= etc
        agua_actual = max(0.0, min(agua_actual, capacidad_campo_mm))

        humedad_porcentaje = round(
            (agua_actual / capacidad_campo_mm) * 100, 1
        )

        agua_facilmente_disponible = (
            capacidad_campo_mm * self.FRACCION_AGUA_DISPONIBLE
        )

        if agua_actual >= agua_facilmente_disponible:
            ks = 1.0
        else:
            ks = round(agua_actual / agua_facilmente_disponible, 3)

        return ks, humedad_porcentaje

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    def _persistir_indicadores(
        self, temporada_parcela_id: str, resultados: list
    ) -> None:
        for r in resultados:
            self.db.execute(
                text("""
                    INSERT INTO indicadores_estres_hidrico (
                        temporada_parcela_id,
                        fecha,
                        nivel_estres,
                        valor_ks,
                        requerimiento_hidrico_etapa_mm,
                        humedad_disponible_mm,
                        dias_hasta_estres_critico,
                        estado_fenologico,
                        created_at
                    ) VALUES (
                        CAST(:tp_id AS uuid),
                        :fecha,
                        :nivel_estres,
                        :valor_ks,
                        :requerimiento,
                        :humedad,
                        NULL,
                        :estado_fenologico,
                        NOW()
                    )
                    ON CONFLICT (temporada_parcela_id, fecha)
                    DO UPDATE SET
                        nivel_estres                    = EXCLUDED.nivel_estres,
                        valor_ks                        = EXCLUDED.valor_ks,
                        requerimiento_hidrico_etapa_mm  = EXCLUDED.requerimiento_hidrico_etapa_mm,
                        humedad_disponible_mm           = EXCLUDED.humedad_disponible_mm,
                        estado_fenologico               = EXCLUDED.estado_fenologico
                """),
                {
                    'tp_id': temporada_parcela_id,
                    'fecha': r['fecha'],
                    'nivel_estres': r['nivel_estres'],
                    'valor_ks': r['ks'],
                    'requerimiento': r['etc_mm'],
                    'humedad': r['humedad_porcentaje'],
                    'estado_fenologico': r['estado_fenologico'],
                }
            )
        self.db.commit()
    # ------------------------------------------------------------------
    # Construcción de respuesta
    # ------------------------------------------------------------------

    def _construir_resumen(
        self,
        temporada_parcela_id: str,
        fecha_inicio: date,
        fecha_fin: date,
        resultados: list
    ) -> dict:
        total_dias = len(resultados)
        dias_con_estres = sum(1 for r in resultados if r['ks'] < 1.0)
        ks_acumulado = sum(r['ks'] for r in resultados)
        ks_promedio = round(
            ks_acumulado / total_dias, 3
        ) if total_dias > 0 else 1.0
        impacto_rendimiento = round((1 - ks_promedio) * 100, 1)

        return {
            'temporada_parcela_id': temporada_parcela_id,
            'fecha_inicio': fecha_inicio.isoformat(),
            'fecha_fin': fecha_fin.isoformat(),
            'total_dias': total_dias,
            'dias_con_estres': dias_con_estres,
            'ks_promedio': ks_promedio,
            'impacto_rendimiento_porcentaje': impacto_rendimiento,
            'interpretacion': self._interpretar_ks(ks_promedio),
            'datos': resultados,
        }

    # ------------------------------------------------------------------
    # Helpers de dominio
    # ------------------------------------------------------------------

    def _calcular_estado(
        self, fecha_siembra, fecha_actual, ciclo_dias
    ) -> str:
        if not fecha_siembra or not ciclo_dias:
            return 'pre_siembra'

        dias = (fecha_actual - fecha_siembra).days

        if dias < 0:
            return 'pre_siembra'

        porcentaje = (dias / ciclo_dias) * 100

        if porcentaje < 5:
            return 'emergencia'
        elif porcentaje < 30:
            return 'crecimiento_vegetativo'
        elif porcentaje < 55:
            return 'floracion'
        elif porcentaje < 80:
            return 'llenado_grano'
        elif porcentaje < 95:
            return 'maduracion'
        return 'cosecha'

    def _obtener_kc(self, estado: str, tp_data) -> float:
        kc_map = {
            'emergencia':             float(tp_data.kc_emergencia or 0.30),
            'crecimiento_vegetativo': float(tp_data.kc_crecimiento or 0.70),
            'floracion':              float(tp_data.kc_floracion or 1.20),
            'llenado_grano':          float(tp_data.kc_llenado_grano or 1.00),
            'maduracion':             float(tp_data.kc_maduracion or 0.60),
            'pre_siembra':            0.0,
            'cosecha':                0.30,
            'post_cosecha':           0.20,
        }
        return kc_map.get(estado, 0.70)

    def _clasificar_estres(self, ks: float) -> str:
        if ks >= 1.0:
            return 'sin_estres'
        elif ks >= 0.75:
            return 'estres_leve'
        elif ks >= 0.50:
            return 'estres_moderado'
        return 'estres_severo'

    def _interpretar_ks(self, ks_promedio: float) -> str:
        if ks_promedio >= 0.95:
            return "Condiciones hidricas excelentes. Rendimiento potencial sin limitaciones por agua."
        elif ks_promedio >= 0.80:
            return "Estres hidrico leve. Reduccion esperada del rendimiento menor al 20 por ciento."
        elif ks_promedio >= 0.60:
            return "Estres hidrico moderado. Reduccion esperada del rendimiento entre 20 y 40 por ciento."
        return "Estres hidrico severo. Reduccion esperada del rendimiento mayor al 40 por ciento."