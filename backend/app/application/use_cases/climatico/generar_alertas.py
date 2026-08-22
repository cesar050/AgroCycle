"""
Caso de uso: CU-CLI-005 Generar Alertas de Humedad.
Analiza el balance hidrico actual de todas las parcelas activas
y genera alertas cuando la humedad baja del umbral critico.
Es el corazon del sistema de alertas de AgroCycle.
"""
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.infrastructure.logging.logger import configurar_logger, log_caso_de_uso

logger = configurar_logger('generar_alertas')


class GenerarAlertasUseCase:
    """
    Implementa CU-CLI-005.
    Revisa el balance hidrico de cada parcela activa
    y genera alertas segun el nivel de humedad estimada.
    """

    UMBRALES = {
        'optima':   (60, 100),
        'moderada': (40, 60),
        'baja':     (20, 40),
        'critica':  (0,  20)
    }

    def __init__(self, db: Session):
        self.db = db

    @log_caso_de_uso('generar_alertas_humedad')
    def ejecutar(self, agricultor_id: str = None) -> dict:
        """
        Genera alertas de humedad para todas las parcelas activas.
        Si se pasa agricultor_id solo procesa sus parcelas.
        """
        filtro = ""
        params = {}
        if agricultor_id:
            filtro = "AND t.agricultor_id = CAST(:agricultor_id AS uuid)"
            params["agricultor_id"] = agricultor_id

        # Obtener parcelas activas con sus datos
        parcelas = self.db.execute(
            text(f"""
                SELECT
                    tp.id as tp_id,
                    tp.parcela_id,
                    tp.estado_fenologico,
                    tp.fecha_siembra,
                    tp.variedad_semilla_id,
                    t.agricultor_id,
                    t.id as temporada_id,
                    p.tipo_suelo_id,
                    p.pendiente_porcentaje,
                    vs.kc_floracion,
                    vs.kc_crecimiento,
                    vs.kc_llenado_grano,
                    vs.ciclo_vegetativo_dias
                FROM temporada_parcelas tp
                JOIN temporadas t ON tp.temporada_id = t.id
                JOIN parcelas p ON tp.parcela_id = p.id
                LEFT JOIN variedades_semilla vs ON tp.variedad_semilla_id = vs.id
                WHERE tp.activo = true
                AND t.estado = 'activa'
                AND tp.fecha_siembra IS NOT NULL
                {filtro}
            """),
            params
        ).fetchall()

        alertas_generadas = []

        for parcela in parcelas:
            alerta = self._evaluar_parcela(parcela)
            if alerta:
                alertas_generadas.append(alerta)
                self._guardar_notificacion(
                    parcela.agricultor_id,
                    alerta
                )

        logger.info(
            f"Alertas generadas: {len(alertas_generadas)} "
            f"de {len(parcelas)} parcelas evaluadas"
        )

        return {
            "total_parcelas_evaluadas": len(parcelas),
            "total_alertas": len(alertas_generadas),
            "alertas": alertas_generadas,
            "fecha_evaluacion": date.today().isoformat()
        }

    def _evaluar_parcela(self, parcela) -> dict:
        """
        Evalua la humedad de una parcela usando los ultimos
        7 dias de datos climaticos disponibles.
        """
        hoy = date.today()
        hace_7_dias = hoy - timedelta(days=7)

        datos = self.db.execute(
            text("""
                SELECT fecha, precipitacion_mm, evapotranspiracion_mm
                FROM datos_climaticos
                WHERE parcela_id = CAST(:parcela_id AS uuid)
                AND fecha BETWEEN :inicio AND :fin
                ORDER BY fecha ASC
            """),
            {
                "parcela_id": str(parcela.parcela_id),
                "inicio": hace_7_dias,
                "fin": hoy
            }
        ).fetchall()

        if not datos:
            return None

        # Calcular humedad estimada simplificada
        precipitacion_total = sum(float(d.precipitacion_mm or 0) for d in datos)
        et0_total = sum(float(d.evapotranspiracion_mm or 0) for d in datos)

        kc = self._obtener_kc(parcela)
        etc_total = et0_total * kc
        pendiente = float(parcela.pendiente_porcentaje or 0)
        factor_escurrimiento = min(pendiente / 100 * 0.5, 0.4)
        precipitacion_efectiva = precipitacion_total * (1 - factor_escurrimiento)

        balance_7_dias = precipitacion_efectiva - etc_total

        # Humedad estimada basada en balance
        if balance_7_dias > 20:
            humedad = 85.0
        elif balance_7_dias > 0:
            humedad = 60.0 + (balance_7_dias / 20) * 25
        elif balance_7_dias > -20:
            humedad = 40.0 + (balance_7_dias / 20) * 20
        elif balance_7_dias > -40:
            humedad = 20.0 + ((balance_7_dias + 20) / 20) * 20
        else:
            humedad = max(0, 20 + balance_7_dias)

        humedad = round(humedad, 1)
        clasificacion = self._clasificar(humedad)

        if clasificacion in ['baja', 'critica']:
            return {
                "temporada_parcela_id": str(parcela.tp_id),
                "parcela_id": str(parcela.parcela_id),
                "estado_fenologico": parcela.estado_fenologico,
                "humedad_estimada": humedad,
                "clasificacion": clasificacion,
                "balance_7_dias_mm": round(balance_7_dias, 1),
                "precipitacion_7_dias_mm": round(precipitacion_total, 1),
                "etc_7_dias_mm": round(etc_total, 1),
                "mensaje": self._generar_mensaje(
                    clasificacion,
                    parcela.estado_fenologico,
                    humedad
                )
            }
        return None

    def _obtener_kc(self, parcela) -> float:
        """Obtiene el Kc segun la etapa fenologica."""
        kc_map = {
            'emergencia': 0.30,
            'crecimiento_vegetativo': float(parcela.kc_crecimiento or 0.70),
            'floracion': float(parcela.kc_floracion or 1.20),
            'llenado_grano': float(parcela.kc_llenado_grano or 1.00),
            'maduracion': 0.60,
            'pre_siembra': 0.0,
            'cosecha': 0.30
        }
        return kc_map.get(parcela.estado_fenologico, 0.70)

    def _clasificar(self, humedad: float) -> str:
        if humedad >= 60:
            return 'optima'
        elif humedad >= 40:
            return 'moderada'
        elif humedad >= 20:
            return 'baja'
        return 'critica'

    def _generar_mensaje(
        self, clasificacion: str, estado: str, humedad: float
    ) -> str:
        etapas_criticas = ['floracion', 'llenado_grano']
        urgencia = "URGENTE" if estado in etapas_criticas else "IMPORTANTE"
        mensajes = {
            'baja': (
                f"{urgencia}: Humedad estimada baja ({humedad}%). "
                f"Su maiz en etapa de {estado} necesita agua. "
                f"Considere riego si tiene disponibilidad."
            ),
            'critica': (
                f"CRITICO: Humedad estimada muy baja ({humedad}%). "
                f"Su maiz en etapa de {estado} esta en estres hidrico severo. "
                f"Riego de emergencia necesario para evitar perdidas."
            )
        }
        return mensajes.get(clasificacion, "")

    def _guardar_notificacion(self, agricultor_id: str, alerta: dict) -> None:
        """Guarda la alerta como notificacion para el agricultor."""
        try:
            # Obtener usuario_id del agricultor
            resultado = self.db.execute(
                text("""
                    SELECT usuario_id FROM agricultores
                    WHERE id = CAST(:agricultor_id AS uuid)
                """),
                {"agricultor_id": str(agricultor_id)}
            ).fetchone()

            if not resultado:
                return

            self.db.execute(
                text("""
                    INSERT INTO notificaciones
                    (id, usuario_id, titulo, mensaje, tipo, referencia_id, referencia_tabla)
                    VALUES (
                        gen_random_uuid(),
                        CAST(:usuario_id AS uuid),
                        :titulo,
                        :mensaje,
                        'alerta_climatica',
                        CAST(:referencia_id AS uuid),
                        'temporada_parcelas'
                    )
                """),
                {
                    "usuario_id": str(resultado.usuario_id),
                    "titulo": f"Alerta de humedad — {alerta['clasificacion'].upper()}",
                    "mensaje": alerta['mensaje'],
                    "referencia_id": alerta['temporada_parcela_id']
                }
            )
            self.db.commit()
        except Exception as e:
            logger.error(f"Error guardando notificacion: {str(e)}")