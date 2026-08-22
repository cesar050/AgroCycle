"""
Recopila todos los datos necesarios para generar la ficha técnica agrícola.
Hace las consultas a la BD y organiza la información en un dict estructurado
que el template HTML puede consumir directamente.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text


class RecopiladorDatosFicha:
    """
    Responsable de obtener y estructurar todos los datos
    de la ficha técnica desde la base de datos.

    Separa la lógica de consulta de la lógica de presentación —
    el template HTML no sabe nada de la BD, solo recibe un dict.
    """

    def __init__(self, db: Session):
        self.db = db

    def recopilar(
        self,
        temporada_parcela_id: str,
        agricultor_id: str,
    ) -> dict:
        info_general = self._info_general(temporada_parcela_id, agricultor_id)

        if not info_general:
            return None

        return {
            'info_general':           info_general,
            'ubicacion':              self._ubicacion(info_general['parcela_id']),
            'condiciones_ambientales': self._condiciones_ambientales(
                info_general['parcela_id'],
                info_general['fecha_siembra'],
            ),
            'suelo':                  self._caracteristicas_suelo(info_general['parcela_id']),
            'requerimientos':         self._requerimientos_cultivo(info_general['variedad_semilla_id']),
            'manejo_agronomico':      self._manejo_agronomico(temporada_parcela_id),
            'parametros_tecnicos':    self._parametros_tecnicos(temporada_parcela_id),
            'desarrollo_cultivo':     self._desarrollo_cultivo(info_general),
            'produccion':             self._produccion(temporada_parcela_id),
            'recomendaciones':        self._recomendaciones(info_general['temporada_id']),
            'productor':              self._info_productor(
                agricultor_id, info_general['temporada_id']
            ),
            # Datos para gráficos
            'humedad_diaria':         self._humedad_diaria(temporada_parcela_id),
            'precipitacion_mensual':  self._precipitacion_mensual(
                info_general['parcela_id'],
                info_general['fecha_siembra'],
            ),
        }
    # ------------------------------------------------------------------
    # Sección 1 — Información general
    # ------------------------------------------------------------------

    def _info_general(
        self, temporada_parcela_id: str, agricultor_id: str
    ) -> dict:
        """
        Obtiene datos básicos del cultivo, variedad y temporada.
        Verifica pertenencia al agricultor en la misma query.
        """
        row = self.db.execute(
            text("""
                SELECT
                    tp.id                           AS tp_id,
                    tp.temporada_id,
                    tp.parcela_id,
                    tp.variedad_semilla_id,
                    tp.fecha_siembra,
                    tp.estado_fenologico,
                    tp.dias_desde_siembra,
                    tp.avance_ciclo_porcentaje,
                    tp.produccion_real_qq,
                    t.nombre                        AS temporada_nombre,
                    t.estado                        AS temporada_estado,
                    t.fecha_inicio,
                    t.fecha_fin_estimada,
                    c.nombre                        AS cultivo_nombre,
                    c.nombre_cientifico,
                    vs.nombre                       AS variedad_nombre,
                    vs.ciclo_vegetativo_dias,
                    vs.produccion_potencial_qq_ha,
                    vs.kc_floracion
                FROM temporada_parcelas tp
                JOIN temporadas t ON tp.temporada_id = t.id
                JOIN agricultores a ON t.agricultor_id = a.id
                JOIN cultivos c ON t.cultivo_id = c.id
                LEFT JOIN variedades_semilla vs ON tp.variedad_semilla_id = vs.id
                WHERE tp.id = CAST(:tp_id AS uuid)
                  AND a.usuario_id = CAST(:agricultor_id AS uuid)
            """),
            {
                'tp_id': temporada_parcela_id,
                'agricultor_id': agricultor_id,
            }
        ).fetchone()

        if not row:
            return None

        return {
            'tp_id': str(row.tp_id),
            'temporada_id': str(row.temporada_id),
            'parcela_id': str(row.parcela_id),
            'variedad_semilla_id': row.variedad_semilla_id,
            'fecha_siembra': str(row.fecha_siembra) if row.fecha_siembra else 'No registrada',
            'estado_fenologico': (row.estado_fenologico or 'pre_siembra').replace('_', ' ').title(),
            'dias_desde_siembra': row.dias_desde_siembra or 0,
            'avance_ciclo_porcentaje': float(row.avance_ciclo_porcentaje or 0),
            'temporada_nombre': row.temporada_nombre,
            'temporada_estado': row.temporada_estado,
            'fecha_inicio': str(row.fecha_inicio),
            'fecha_fin_estimada': str(row.fecha_fin_estimada) if row.fecha_fin_estimada else 'Por definir',
            'cultivo_nombre': row.cultivo_nombre,
            'nombre_cientifico': row.nombre_cientifico or '',
            'variedad_nombre': row.variedad_nombre or 'Sin variedad registrada',
            'ciclo_vegetativo_dias': row.ciclo_vegetativo_dias or 0,
            'produccion_potencial_qq_ha': float(row.produccion_potencial_qq_ha or 0),
        }

    # ------------------------------------------------------------------
    # Sección 2 — Ubicación de la parcela
    # ------------------------------------------------------------------

    def _ubicacion(self, parcela_id: str) -> dict:
        """
        Obtiene datos de ubicación incluyendo coordenadas del centroide
        calculadas automáticamente por PostGIS desde el polígono.
        """
        row = self.db.execute(
            text("""
                SELECT
                    p.nombre                        AS parcela_nombre,
                    p.superficie_ha,
                    p.altitud_promedio_msnm,
                    p.pendiente_porcentaje,
                    p.orientacion,
                    p.drenaje,
                    p.acceso_riego,
                    p.tipo_riego,
                    ts.nombre                       AS tipo_suelo_nombre,
                    l.nombre                        AS lote_nombre,
                    f.nombre                        AS finca_nombre,
                    f.sector,
                    f.parroquia,
                    f.canton,
                    f.provincia,
                    ST_Y(ST_Centroid(p.geometria))  AS latitud,
                    ST_X(ST_Centroid(p.geometria))  AS longitud
                FROM parcelas p
                JOIN lotes l ON p.lote_id = l.id
                JOIN fincas f ON l.finca_id = f.id
                LEFT JOIN tipos_suelo ts ON p.tipo_suelo_id = ts.id
                WHERE p.id = CAST(:parcela_id AS uuid)
            """),
            {'parcela_id': parcela_id}
        ).fetchone()

        if not row:
            return {}

        return {
            'parcela_nombre': row.parcela_nombre,
            'superficie_ha': float(row.superficie_ha or 0),
            'superficie_m2': round(float(row.superficie_ha or 0) * 10000, 0),
            'altitud_msnm': float(row.altitud_promedio_msnm or 0),
            'pendiente_porcentaje': float(row.pendiente_porcentaje or 0),
            'orientacion': row.orientacion or 'No determinada',
            'drenaje': row.drenaje or 'No registrado',
            'acceso_riego': 'Si' if row.acceso_riego else 'No',
            'tipo_riego': row.tipo_riego or 'Ninguno',
            'tipo_suelo': row.tipo_suelo_nombre or 'No registrado',
            'lote_nombre': row.lote_nombre,
            'finca_nombre': row.finca_nombre,
            'sector': row.sector or '',
            'parroquia': row.parroquia or '',
            'canton': row.canton or '',
            'provincia': row.provincia or '',
            'latitud': round(float(row.latitud), 6) if row.latitud else None,
            'longitud': round(float(row.longitud), 6) if row.longitud else None,
        }

    # ------------------------------------------------------------------
    # Sección 3 — Condiciones ambientales
    # ------------------------------------------------------------------

    def _condiciones_ambientales(
        self, parcela_id: str, fecha_siembra
    ) -> dict:
        """
        Obtiene resumen climático desde la fecha de siembra hasta hoy.
        Usa datos reales de Open-Meteo almacenados en datos_climaticos.
        """
        row = self.db.execute(
            text("""
                SELECT
                    AVG(temperatura_promedio_c)     AS temp_promedio,
                    MAX(temperatura_max_c)          AS temp_maxima,
                    MIN(temperatura_min_c)          AS temp_minima,
                    SUM(precipitacion_mm)           AS precip_total,
                    AVG(humedad_relativa_porcentaje) AS humedad_promedio,
                    AVG(velocidad_viento_km_h)      AS viento_promedio,
                    AVG(radiacion_solar_mj_m2)      AS radiacion_promedio,
                    COUNT(CASE WHEN precipitacion_mm > 0 THEN 1 END) AS dias_con_lluvia,
                    COUNT(*) AS total_dias
                FROM datos_climaticos
                WHERE parcela_id = CAST(:parcela_id AS uuid)
                  AND fecha >= :fecha_inicio
            """),
            {
                'parcela_id': parcela_id,
                'fecha_inicio': fecha_siembra if fecha_siembra != 'No registrada' else '2025-01-01',
            }
        ).fetchone()

        if not row or not row.temp_promedio:
            return {'sin_datos': True}

        return {
            'temp_promedio': round(float(row.temp_promedio), 1),
            'temp_maxima': round(float(row.temp_maxima), 1),
            'temp_minima': round(float(row.temp_minima), 1),
            'precip_total_mm': round(float(row.precip_total or 0), 1),
            'humedad_promedio': round(float(row.humedad_promedio or 0), 1),
            'viento_promedio_km_h': round(float(row.viento_promedio or 0), 1),
            'radiacion_promedio': round(float(row.radiacion_promedio or 0), 1),
            'dias_con_lluvia': int(row.dias_con_lluvia or 0),
            'total_dias': int(row.total_dias or 0),
        }

    # ------------------------------------------------------------------
    # Sección 4 — Características del suelo
    # ------------------------------------------------------------------

    def _caracteristicas_suelo(self, parcela_id: str) -> dict:
        """
        Obtiene características del suelo registradas por el agricultor
        y calculadas automáticamente por el sistema.
        """
        row = self.db.execute(
            text("""
                SELECT
                    ts.nombre                       AS tipo_suelo,
                    ts.capacidad_retencion_agua,
                    p.pendiente_porcentaje,
                    p.drenaje,
                    p.altitud_promedio_msnm,
                    p.presencia_piedras,
                    p.observaciones
                FROM parcelas p
                LEFT JOIN tipos_suelo ts ON p.tipo_suelo_id = ts.id
                WHERE p.id = CAST(:parcela_id AS uuid)
            """),
            {'parcela_id': parcela_id}
        ).fetchone()

        if not row:
            return {}

        capacidad = float(row.capacidad_retencion_agua or 0.15)

        return {
            'tipo_suelo': row.tipo_suelo or 'No registrado',
            'capacidad_retencion_agua': capacidad,
            'agua_disponible_mm_m': round(capacidad * 1000, 0),
            'pendiente_porcentaje': float(row.pendiente_porcentaje or 0),
            'drenaje': row.drenaje or 'No registrado',
            'altitud_msnm': float(row.altitud_promedio_msnm or 0),
            'presencia_piedras': 'Si' if row.presencia_piedras else 'No',
            'observaciones': row.observaciones or 'Sin observaciones adicionales',
        }

    # ------------------------------------------------------------------
    # Sección 5 — Requerimientos del cultivo
    # ------------------------------------------------------------------

    def _requerimientos_cultivo(
        self, variedad_semilla_id: int
    ) -> dict:
        """
        Obtiene requerimientos técnicos de la variedad desde el catálogo.
        Columnas verificadas contra la tabla real en PostgreSQL.
        """
        if not variedad_semilla_id:
            return {'sin_variedad': True}

        row = self.db.execute(
            text("""
                SELECT
                    vs.nombre,
                    vs.ciclo_vegetativo_dias,
                    vs.produccion_potencial_qq_ha,
                    vs.kc_emergencia,
                    vs.kc_crecimiento,
                    vs.kc_floracion,
                    vs.kc_llenado_grano,
                    vs.kc_maduracion,
                    vs.temp_optima_min,
                    vs.temp_optima_max,
                    vs.densidad_plantas_min,
                    vs.densidad_plantas_max,
                    vs.humedad_suelo_optima_min,
                    vs.humedad_suelo_optima_max,
                    vs.tolerancia_sequia,
                    vs.adaptacion_zona,
                    vs.precipitacion_ciclo_min_mm,
                    vs.precipitacion_ciclo_max_mm
                FROM variedades_semilla vs
                WHERE vs.id = :variedad_id
            """),
            {'variedad_id': variedad_semilla_id}
        ).fetchone()

        if not row:
            return {'sin_variedad': True}

        return {
            'variedad': row.nombre,
            'ciclo_dias': row.ciclo_vegetativo_dias,
            'produccion_potencial_qq_ha': float(row.produccion_potencial_qq_ha or 0),
            'kc_por_etapa': {
                'emergencia':             float(row.kc_emergencia or 0.30),
                'crecimiento_vegetativo': float(row.kc_crecimiento or 0.70),
                'floracion':              float(row.kc_floracion or 1.20),
                'llenado_grano':          float(row.kc_llenado_grano or 1.00),
                'maduracion':             float(row.kc_maduracion or 0.60),
            },
            'temp_optima_min': float(row.temp_optima_min or 18),
            'temp_optima_max': float(row.temp_optima_max or 32),
            'densidad_min': int(row.densidad_plantas_min or 50000),
            'densidad_max': int(row.densidad_plantas_max or 70000),
            'humedad_optima_min': float(row.humedad_suelo_optima_min or 60),
            'humedad_optima_max': float(row.humedad_suelo_optima_max or 80),
            'tolerancia_sequia': row.tolerancia_sequia or 'No registrada',
            'adaptacion_zona': row.adaptacion_zona or 'No registrada',
            'precipitacion_min_mm': float(row.precipitacion_ciclo_min_mm or 0),
            'precipitacion_max_mm': float(row.precipitacion_ciclo_max_mm or 0),
        }
    # ------------------------------------------------------------------
    # Sección 6 — Manejo agronómico
    # ------------------------------------------------------------------

    def _manejo_agronomico(self, temporada_parcela_id: str) -> dict:
        """
        Obtiene resumen de actividades agronómicas registradas.
        Agrupa por tipo para el resumen de la ficha.
        """
        rows = self.db.execute(
            text("""
                SELECT
                    ta.nombre           AS tipo,
                    COUNT(*)            AS cantidad,
                    MIN(a.fecha)        AS primera,
                    MAX(a.fecha)        AS ultima,
                    SUM(a.costo_total)  AS costo_total
                FROM actividades a
                JOIN tipos_actividad ta ON a.tipo_actividad_id = ta.id
                WHERE a.temporada_id = (
                    SELECT temporada_id FROM temporada_parcelas
                    WHERE id = CAST(:tp_id AS uuid)
                )
                GROUP BY ta.nombre
                ORDER BY MIN(a.fecha)
            """),
            {'tp_id': temporada_parcela_id}
        ).fetchall()

        actividades = [
            {
                'tipo': r.tipo,
                'cantidad': int(r.cantidad),
                'primera': str(r.primera),
                'ultima': str(r.ultima),
                'costo_total': round(float(r.costo_total or 0), 2),
            }
            for r in rows
        ]

        return {
            'actividades': actividades,
            'total_actividades': sum(a['cantidad'] for a in actividades),
            'costo_total_actividades': round(
                sum(a['costo_total'] for a in actividades), 2
            ),
        }

    # ------------------------------------------------------------------
    # Sección 7 — Parámetros técnicos FAO
    # ------------------------------------------------------------------

    def _parametros_tecnicos(self, temporada_parcela_id: str) -> dict:
        """
        Obtiene indicadores FAO-56 calculados por el módulo climático.
        Ks promedio por etapa fenológica para la tabla técnica.
        """
        rows = self.db.execute(
            text("""
                SELECT
                    estado_fenologico           AS etapa,
                    AVG(valor_ks)               AS ks_promedio,
                    AVG(requerimiento_hidrico_etapa_mm) AS etc_promedio,
                    AVG(humedad_disponible_mm)  AS humedad_promedio,
                    COUNT(*)                    AS dias
                FROM indicadores_estres_hidrico
                WHERE temporada_parcela_id = CAST(:tp_id AS uuid)
                  AND estado_fenologico IS NOT NULL
                GROUP BY estado_fenologico
                ORDER BY MIN(fecha)
            """),
            {'tp_id': temporada_parcela_id}
        ).fetchall()

        return {
            'por_etapa': [
                {
                    'etapa': r.etapa.replace('_', ' ').title(),
                    'ks_promedio': round(float(r.ks_promedio or 1), 3),
                    'etc_promedio_mm': round(float(r.etc_promedio or 0), 2),
                    'humedad_promedio': round(float(r.humedad_promedio or 0), 1),
                    'dias': int(r.dias),
                }
                for r in rows
            ]
        }

    # ------------------------------------------------------------------
    # Sección 8 — Desarrollo del cultivo
    # ------------------------------------------------------------------

    def _desarrollo_cultivo(self, info_general: dict) -> dict:
        """
        Construye el timeline fenológico del cultivo.
        Usa los datos de info_general para calcular los rangos de días.
        """
        ciclo = info_general['ciclo_vegetativo_dias']

        etapas = [
            {
                'nombre': 'Emergencia',
                'rango_dias': f"0 - {int(ciclo * 0.05)} DDS",
                'porcentaje': '0 - 5%',
            },
            {
                'nombre': 'Crecimiento Vegetativo',
                'rango_dias': f"{int(ciclo * 0.05)} - {int(ciclo * 0.30)} DDS",
                'porcentaje': '5 - 30%',
            },
            {
                'nombre': 'Floracion',
                'rango_dias': f"{int(ciclo * 0.30)} - {int(ciclo * 0.55)} DDS",
                'porcentaje': '30 - 55%',
            },
            {
                'nombre': 'Llenado de Grano',
                'rango_dias': f"{int(ciclo * 0.55)} - {int(ciclo * 0.80)} DDS",
                'porcentaje': '55 - 80%',
            },
            {
                'nombre': 'Maduracion',
                'rango_dias': f"{int(ciclo * 0.80)} - {int(ciclo * 0.95)} DDS",
                'porcentaje': '80 - 95%',
            },
            {
                'nombre': 'Cosecha',
                'rango_dias': f"{int(ciclo * 0.95)} - {ciclo} DDS",
                'porcentaje': '95 - 100%',
            },
        ]

        return {
            'etapas': etapas,
            'etapa_actual': info_general['estado_fenologico'],
            'dias_desde_siembra': info_general['dias_desde_siembra'],
            'avance_porcentaje': info_general['avance_ciclo_porcentaje'],
            'ciclo_total_dias': ciclo,
        }

    # ------------------------------------------------------------------
    # Sección 9 — Producción esperada
    # ------------------------------------------------------------------

    def _produccion(self, temporada_parcela_id: str) -> dict:
        """
        Obtiene la última estimación de producción y la producción real
        si la temporada ya fue cerrada.
        """
        row = self.db.execute(
            text("""
                SELECT
                    ep.valor_qq_ha,
                    ep.valor_total_qq,
                    ep.margen_error_porcentaje,
                    ep.valor_minimo_qq_ha,
                    ep.valor_maximo_qq_ha,
                    ep.algoritmo_usado,
                    ep.fecha_generacion,
                    tp.produccion_real_qq,
                    tp.fecha_cosecha,
                    tp.precio_venta_qq
                FROM estimaciones_produccion ep
                JOIN temporada_parcelas tp ON ep.temporada_parcela_id = tp.id
                WHERE ep.temporada_parcela_id = CAST(:tp_id AS uuid)
                ORDER BY ep.fecha_generacion DESC
                LIMIT 1
            """),
            {'tp_id': temporada_parcela_id}
        ).fetchone()

        if not row:
            return {'sin_estimacion': True}

        return {
            'valor_estimado_qq_ha': float(row.valor_qq_ha),
            'valor_total_estimado_qq': float(row.valor_total_qq or 0),
            'margen_error': float(row.margen_error_porcentaje or 0),
            'rango_minimo_qq_ha': float(row.valor_minimo_qq_ha or 0),
            'rango_maximo_qq_ha': float(row.valor_maximo_qq_ha or 0),
            'algoritmo': row.algoritmo_usado,
            'fecha_estimacion': str(row.fecha_generacion)[:10],
            'produccion_real_qq': float(row.produccion_real_qq) if row.produccion_real_qq else None,
            'fecha_cosecha': str(row.fecha_cosecha) if row.fecha_cosecha else None,
            'precio_venta_qq': float(row.precio_venta_qq) if row.precio_venta_qq else None,
        }

    # ------------------------------------------------------------------
    # Sección 11 — Recomendaciones técnicas
    # ------------------------------------------------------------------

    def _recomendaciones(self, temporada_id: str) -> list:
        """
        Obtiene recomendaciones del agrónomo pendientes de implementar.
        Solo las no implementadas para que aparezcan como acciones vigentes.
        """
        rows = self.db.execute(
            text("""
                SELECT
                    ra.descripcion,
                    ra.urgencia,
                    ra.tipo,
                    ra.fecha,
                    ra.fecha_limite
                FROM recomendaciones_agronomicas ra
                WHERE ra.temporada_id = CAST(:temporada_id AS uuid)
                  AND ra.implementada = false
                ORDER BY
                    CASE ra.urgencia
                        WHEN 'alta' THEN 1
                        WHEN 'media' THEN 2
                        WHEN 'baja' THEN 3
                    END,
                    ra.fecha DESC
            """),
            {'temporada_id': temporada_id}
        ).fetchall()

        return [
            {
                'descripcion': r.descripcion,
                'urgencia': r.urgencia,
                'tipo': r.tipo or 'General',
                'fecha': str(r.fecha),
                'fecha_limite': str(r.fecha_limite) if r.fecha_limite else None,
            }
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Sección 13 — Información del productor
    # ------------------------------------------------------------------

    def _info_productor(
        self, agricultor_id: str, temporada_id: str
    ) -> dict:
        """
        Obtiene datos del agricultor y del agrónomo vinculado si existe.
        """
        row = self.db.execute(
            text("""
                SELECT
                    u.nombre || ' ' || u.apellido   AS agricultor_nombre,
                    u.correo                        AS agricultor_correo,
                    ag.telefono                     AS agricultor_telefono
                FROM usuarios u
                JOIN agricultores ag ON u.id = ag.usuario_id
                WHERE u.id = CAST(:usuario_id AS uuid)
            """),
            {'usuario_id': agricultor_id}
        ).fetchone()

        agronomo = self.db.execute(
            text("""
                SELECT
                    u.nombre || ' ' || u.apellido   AS agronomo_nombre,
                    a.numero_registro,
                    a.especialidad
                FROM finca_agronomo fa
                JOIN agronomos a ON fa.agronomo_id = a.id
                JOIN usuarios u ON a.usuario_id = u.id
                JOIN temporadas t ON fa.finca_id = t.finca_id
                WHERE t.id = CAST(:temporada_id AS uuid)
                  AND fa.activo = true
                LIMIT 1
            """),
            {'temporada_id': temporada_id}
        ).fetchone()

        return {
            'agricultor': {
                'nombre': row.agricultor_nombre if row else 'No registrado',
                'correo': row.agricultor_correo if row else '',
                'telefono': row.agricultor_telefono if row else '',
            },
            'agronomo': {
                'nombre': agronomo.agronomo_nombre if agronomo else 'Sin agronomo vinculado',
                'numero_registro': agronomo.numero_registro if agronomo else '',
                'especialidad': agronomo.especialidad if agronomo else '',
            } if agronomo else None,
        }

    # ------------------------------------------------------------------
    # Datos para gráficos
    # ------------------------------------------------------------------

    def _humedad_diaria(self, temporada_parcela_id: str) -> list:
        """
        Obtiene la humedad del suelo día a día desde
        indicadores_estres_hidrico para el gráfico de línea.
        """
        rows = self.db.execute(
            text("""
                SELECT
                    TO_CHAR(fecha, 'DD/MM') AS fecha,
                    COALESCE(humedad_disponible_mm, 0) AS humedad_porcentaje
                FROM indicadores_estres_hidrico
                WHERE temporada_parcela_id = CAST(:tp_id AS uuid)
                ORDER BY fecha ASC
            """),
            {'tp_id': temporada_parcela_id}
        ).fetchall()

        return [
            {
                'fecha': r.fecha,
                'humedad_porcentaje': float(r.humedad_porcentaje),
            }
            for r in rows
        ]

    def _precipitacion_mensual(
        self, parcela_id: str, fecha_siembra
    ) -> list:
        """
        Agrupa la precipitación por mes desde la fecha de siembra.
        Datos reales de Open-Meteo almacenados en datos_climaticos.
        """
        rows = self.db.execute(
            text("""
                SELECT
                    TO_CHAR(DATE_TRUNC('month', fecha), 'Mon YYYY') AS mes,
                    SUM(precipitacion_mm) AS precipitacion_mm
                FROM datos_climaticos
                WHERE parcela_id = CAST(:parcela_id AS uuid)
                  AND fecha >= :fecha_inicio
                GROUP BY DATE_TRUNC('month', fecha)
                ORDER BY DATE_TRUNC('month', fecha)
            """),
            {
                'parcela_id': parcela_id,
                'fecha_inicio': fecha_siembra if fecha_siembra != 'No registrada' else '2025-01-01',
            }
        ).fetchall()

        return [
            {
                'mes': r.mes,
                'precipitacion_mm': round(float(r.precipitacion_mm or 0), 1),
            }
            for r in rows
        ]