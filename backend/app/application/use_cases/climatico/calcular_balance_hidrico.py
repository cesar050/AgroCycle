"""
Caso de uso: Calcular Balance Hidrico FAO-56.
Calcula la humedad del suelo dia a dia usando la ecuacion
del balance hidrico de la FAO-56 sin sensores fisicos.

Formula principal:
    Dr(i) = Dr(i-1) - Pe(i) - Ir(i) + ETc(i) + DP(i)

Donde:
    Dr  = Deficit de agua en la zona radicular (mm)
    Pe  = Precipitacion efectiva (mm)
    Ir  = Riego aplicado (mm)
    ETc = Evapotranspiracion del cultivo = ET0 x Kc
    DP  = Percolacion profunda (mm)
"""
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.infrastructure.logging.logger import configurar_logger, log_caso_de_uso

logger = configurar_logger('balance_hidrico')


class CalcularBalanceHidricoUseCase:
    """
    Implementa el balance hidrico FAO-56 para estimar
    la humedad del suelo de una parcela dia a dia.
    Usa datos climaticos de Open-Meteo ya descargados
    y la ficha tecnica de la variedad de semilla sembrada.
    """

    # Capacidad de agua disponible total por tipo de suelo (mm/m)
    AGUA_DISPONIBLE_SUELO = {
        1: 120,  # Franco arenoso
        2: 220,  # Franco arcilloso
        3: 180,  # Franco limoso
        4: 280,  # Arcilloso
        5: 80,   # Arenoso
        6: 200,  # Franco
    }

    # Profundidad radicular del maiz por etapa fenologica (m)
    PROFUNDIDAD_RADICULAR = {
        'pre_siembra': 0.0,
        'emergencia': 0.15,
        'crecimiento_vegetativo': 0.50,
        'floracion': 0.80,
        'llenado_grano': 0.80,
        'maduracion': 0.70,
        'cosecha': 0.50,
        'post_cosecha': 0.0
    }

    def __init__(self, db: Session):
        self.db = db

    @log_caso_de_uso('calcular_balance_hidrico')
    def ejecutar(
        self,
        temporada_parcela_id: str,
        parcela_id: str,
        fecha_inicio: date,
        fecha_fin: date
    ) -> dict:
        """
        Calcula el balance hidrico para un rango de fechas.
        Paso 1: Obtener datos de la parcela y la variedad sembrada.
        Paso 2: Obtener datos climaticos del periodo.
        Paso 3: Calcular balance hidrico dia a dia.
        Paso 4: Guardar indicadores de humedad.
        Paso 5: Generar alertas si humedad baja del umbral.
        """
        # Paso 1: Obtener datos de la temporada parcela
        tp_data = self.db.execute(
            text("""
                SELECT 
                    tp.estado_fenologico,
                    tp.fecha_siembra,
                    tp.variedad_semilla_id,
                    vs.kc_emergencia,
                    vs.kc_crecimiento,
                    vs.kc_floracion,
                    vs.kc_llenado_grano,
                    vs.kc_maduracion,
                    vs.ciclo_vegetativo_dias,
                    p.tipo_suelo_id,
                    p.pendiente_porcentaje,
                    p.superficie_ha
                FROM temporada_parcelas tp
                LEFT JOIN variedades_semilla vs ON tp.variedad_semilla_id = vs.id
                LEFT JOIN parcelas p ON tp.parcela_id = CAST(:parcela_id AS uuid)
                WHERE tp.id = CAST(:tp_id AS uuid)
            """),
            {"tp_id": temporada_parcela_id, "parcela_id": parcela_id}
        ).fetchone()

        if not tp_data:
            raise ValueError("TemporadaParcela no encontrada")

        # Paso 2: Obtener datos climaticos del periodo
        datos_climaticos = self.db.execute(
            text("""
                SELECT fecha, precipitacion_mm, evapotranspiracion_mm
                FROM datos_climaticos
                WHERE parcela_id = CAST(:parcela_id AS uuid)
                AND fecha BETWEEN :fecha_inicio AND :fecha_fin
                ORDER BY fecha ASC
            """),
            {
                "parcela_id": parcela_id,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin
            }
        ).fetchall()

        if not datos_climaticos:
            raise ValueError("No hay datos climaticos para el periodo indicado")

        # Paso 3: Calcular balance hidrico dia a dia
        tipo_suelo_id = tp_data.tipo_suelo_id or 6
        agua_disponible_mm_m = float(self.AGUA_DISPONIBLE_SUELO.get(tipo_suelo_id, 200))
        pendiente = float(tp_data.pendiente_porcentaje or 0)

        resultados = []
        humedad_anterior = 70.0  # Humedad inicial asumida 70%
        alertas = []

        for dato in datos_climaticos:
            fecha = dato.fecha
            precipitacion = float(dato.precipitacion_mm or 0)
            et0 = float(dato.evapotranspiracion_mm or 0)

            # Determinar etapa fenologica y Kc
            estado_fenologico = self._calcular_estado_fenologico(
                tp_data.fecha_siembra, fecha, tp_data.ciclo_vegetativo_dias
            )
            kc = self._obtener_kc(estado_fenologico, tp_data)

            # Calcular ETc — consumo real del cultivo
            etc = et0 * kc

            # Calcular precipitacion efectiva
            # La pendiente reduce la infiltracion
            factor_escurrimiento = min(pendiente / 100 * 0.5, 0.4)
            precipitacion_efectiva = precipitacion * (1 - factor_escurrimiento)

            # Profundidad radicular segun etapa
            prof_radicular = self.PROFUNDIDAD_RADICULAR.get(estado_fenologico, 0.5)
            capacidad_campo_mm = agua_disponible_mm_m * prof_radicular

            if capacidad_campo_mm == 0:
                humedad_porcentaje = humedad_anterior
            else:
                # Balance hidrico diario
                agua_disponible_hoy = (humedad_anterior / 100) * capacidad_campo_mm
                agua_disponible_hoy += precipitacion_efectiva
                agua_disponible_hoy -= etc
                agua_disponible_hoy = max(0, min(agua_disponible_hoy, capacidad_campo_mm))
                humedad_porcentaje = round(
                    (agua_disponible_hoy / capacidad_campo_mm) * 100, 1
                ) if capacidad_campo_mm > 0 else humedad_anterior

            # Clasificar humedad
            clasificacion = self._clasificar_humedad(humedad_porcentaje)

            resultado_dia = {
                "fecha": str(fecha),
                "estado_fenologico": estado_fenologico,
                "kc": kc,
                "et0_mm": round(et0, 2),
                "etc_mm": round(etc, 2),
                "precipitacion_mm": round(precipitacion, 2),
                "precipitacion_efectiva_mm": round(precipitacion_efectiva, 2),
                "humedad_estimada_porcentaje": humedad_porcentaje,
                "clasificacion": clasificacion
            }
            resultados.append(resultado_dia)

            # Generar alerta si humedad critica
            if clasificacion in ['baja', 'critica']:
                alertas.append({
                    "fecha": str(fecha),
                    "humedad": humedad_porcentaje,
                    "clasificacion": clasificacion,
                    "mensaje": self._generar_mensaje_alerta(
                        clasificacion, estado_fenologico, humedad_porcentaje
                    )
                })

            humedad_anterior = humedad_porcentaje

        logger.info(
            f"Balance hidrico calculado: {len(resultados)} dias, "
            f"{len(alertas)} alertas generadas"
        )

        return {
            "temporada_parcela_id": temporada_parcela_id,
            "fecha_inicio": fecha_inicio.isoformat(),
            "fecha_fin": fecha_fin.isoformat(),
            "total_dias": len(resultados),
            "total_alertas": len(alertas),
            "alertas": alertas,
            "datos": resultados
        }

    def _calcular_estado_fenologico(
        self, fecha_siembra, fecha_actual, ciclo_dias
    ) -> str:
        """Calcula la etapa fenologica segun los dias desde la siembra."""
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
        else:
            return 'cosecha'

    def _obtener_kc(self, estado_fenologico: str, tp_data) -> float:
        """Obtiene el Kc segun la etapa fenologica y la variedad."""
        kc_map = {
            'emergencia': float(tp_data.kc_emergencia or 0.30),
            'crecimiento_vegetativo': float(tp_data.kc_crecimiento or 0.70),
            'floracion': float(tp_data.kc_floracion or 1.20),
            'llenado_grano': float(tp_data.kc_llenado_grano or 1.00),
            'maduracion': float(tp_data.kc_maduracion or 0.60),
            'pre_siembra': 0.0,
            'cosecha': 0.30
        }
        return kc_map.get(estado_fenologico, 0.70)

    def _clasificar_humedad(self, humedad: float) -> str:
        """Clasifica el nivel de humedad del suelo."""
        if humedad >= 60:
            return 'optima'
        elif humedad >= 40:
            return 'moderada'
        elif humedad >= 20:
            return 'baja'
        else:
            return 'critica'

    def _generar_mensaje_alerta(
        self, clasificacion: str, estado: str, humedad: float
    ) -> str:
        """Genera un mensaje de alerta comprensible para el agricultor."""
        etapas_criticas = ['floracion', 'llenado_grano']
        urgencia = "URGENTE" if estado in etapas_criticas else "IMPORTANTE"

        mensajes = {
            'baja': (
                f"{urgencia}: Humedad del suelo baja ({humedad}%). "
                f"Su cultivo en etapa de {estado} necesita agua. "
                f"Considere riego si tiene disponibilidad."
            ),
            'critica': (
                f"CRITICO: Humedad del suelo muy baja ({humedad}%). "
                f"Su cultivo en etapa de {estado} esta en estres hidrico severo. "
                f"Riego de emergencia necesario para evitar perdidas."
            )
        }
        return mensajes.get(clasificacion, "Monitorear humedad del suelo")