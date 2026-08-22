"""
CU-CLI-006 — Historial climático paginado con filtros.

Permite al agricultor consultar el historial de datos climáticos
de una parcela con filtros de fecha y paginación para no cargar
los 151 días de una vez en el frontend.
"""
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.infrastructure.logging.logger import log_caso_de_uso


class HistorialClimaticoUseCase:
    """
    Implementa CU-CLI-006.

    Responsabilidades:
    1. Verificar que la parcela pertenece al agricultor
    2. Retornar datos climáticos paginados con filtros
    3. Incluir resumen estadístico del período consultado
    """

    def __init__(self, db: Session):
        self.db = db

    @log_caso_de_uso('CU-CLI-006 Historial Climático Paginado')
    def ejecutar(
        self,
        parcela_id: str,
        agricultor_id: str,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        fuente: Optional[str] = None,
        pagina: int = 1,
        por_pagina: int = 30,
    ) -> tuple:
        """
        Retorna historial climático paginado.

        Args:
            parcela_id: UUID de la parcela
            agricultor_id: UUID del usuario autenticado
            fecha_inicio: filtro desde esta fecha
            fecha_fin: filtro hasta esta fecha
            fuente: filtrar por 'api', 'manual' o 'interpolado'
            pagina: número de página (empieza en 1)
            por_pagina: registros por página (máximo 90)

        Returns:
            tuple (dict con datos paginados, int código HTTP)
        """
        # 1. Verificar pertenencia
        parcela = self._verificar_parcela(parcela_id, agricultor_id)

        if not parcela:
            return {
                'error': 'Parcela no encontrada o no pertenece al agricultor.'
            }, 404

        # 2. Limitar por_pagina para no sobrecargar
        por_pagina = min(por_pagina, 90)
        offset = (pagina - 1) * por_pagina

        # 3. Obtener total de registros para la paginación
        total = self._contar_registros(
            parcela_id, fecha_inicio, fecha_fin, fuente
        )

        # 4. Obtener datos paginados
        datos = self._obtener_datos(
            parcela_id, fecha_inicio, fecha_fin,
            fuente, por_pagina, offset
        )

        # 5. Resumen estadístico del período
        resumen = self._resumen_periodo(
            parcela_id, fecha_inicio, fecha_fin
        )

        total_paginas = (total + por_pagina - 1) // por_pagina

        return {
            'parcela_id': parcela_id,
            'parcela_nombre': parcela['nombre'],
            'paginacion': {
                'pagina_actual': pagina,
                'por_pagina': por_pagina,
                'total_registros': total,
                'total_paginas': total_paginas,
                'tiene_siguiente': pagina < total_paginas,
                'tiene_anterior': pagina > 1,
            },
            'filtros': {
                'fecha_inicio': str(fecha_inicio) if fecha_inicio else None,
                'fecha_fin': str(fecha_fin) if fecha_fin else None,
                'fuente': fuente,
            },
            'resumen': resumen,
            'datos': datos,
        }, 200

    def _verificar_parcela(
        self, parcela_id: str, agricultor_id: str
    ) -> Optional[dict]:
        """Verifica que la parcela pertenece al agricultor."""
        row = self.db.execute(
            text("""
                SELECT p.id, p.nombre
                FROM parcelas p
                JOIN lotes l        ON p.lote_id = l.id
                JOIN fincas f       ON l.finca_id = f.id
                JOIN agricultores a ON f.agricultor_id = a.id
                WHERE p.id = CAST(:parcela_id AS uuid)
                  AND a.usuario_id = CAST(:agricultor_id AS uuid)
            """),
            {
                'parcela_id': parcela_id,
                'agricultor_id': agricultor_id,
            }
        ).fetchone()

        if not row:
            return None

        return {'id': str(row.id), 'nombre': row.nombre}

    def _contar_registros(
        self,
        parcela_id: str,
        fecha_inicio: Optional[date],
        fecha_fin: Optional[date],
        fuente: Optional[str],
    ) -> int:
        """Cuenta el total de registros para calcular páginas."""
        filtros = self._construir_filtros(
            fecha_inicio, fecha_fin, fuente
        )

        row = self.db.execute(
            text(f"""
                SELECT COUNT(*) AS total
                FROM datos_climaticos
                WHERE parcela_id = CAST(:parcela_id AS uuid)
                {filtros}
            """),
            {
                'parcela_id': parcela_id,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'fuente': fuente,
            }
        ).fetchone()

        return int(row.total or 0)

    def _obtener_datos(
        self,
        parcela_id: str,
        fecha_inicio: Optional[date],
        fecha_fin: Optional[date],
        fuente: Optional[str],
        limite: int,
        offset: int,
    ) -> list:
        """Obtiene los datos climáticos paginados."""
        filtros = self._construir_filtros(
            fecha_inicio, fecha_fin, fuente
        )

        rows = self.db.execute(
            text(f"""
                SELECT
                    fecha,
                    precipitacion_mm,
                    temperatura_max_c,
                    temperatura_min_c,
                    temperatura_promedio_c,
                    humedad_relativa_porcentaje,
                    evapotranspiracion_mm,
                    velocidad_viento_km_h,
                    radiacion_solar_mj_m2,
                    fuente
                FROM datos_climaticos
                WHERE parcela_id = CAST(:parcela_id AS uuid)
                {filtros}
                ORDER BY fecha DESC
                LIMIT :limite OFFSET :offset
            """),
            {
                'parcela_id': parcela_id,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'fuente': fuente,
                'limite': limite,
                'offset': offset,
            }
        ).fetchall()

        return [
            {
                'fecha': str(r.fecha),
                'precipitacion_mm': float(r.precipitacion_mm or 0),
                'temperatura_max_c': float(r.temperatura_max_c) if r.temperatura_max_c else None,
                'temperatura_min_c': float(r.temperatura_min_c) if r.temperatura_min_c else None,
                'temperatura_promedio_c': float(r.temperatura_promedio_c) if r.temperatura_promedio_c else None,
                'humedad_relativa_porcentaje': float(r.humedad_relativa_porcentaje) if r.humedad_relativa_porcentaje else None,
                'evapotranspiracion_mm': float(r.evapotranspiracion_mm) if r.evapotranspiracion_mm else None,
                'velocidad_viento_km_h': float(r.velocidad_viento_km_h) if r.velocidad_viento_km_h else None,
                'radiacion_solar_mj_m2': float(r.radiacion_solar_mj_m2) if r.radiacion_solar_mj_m2 else None,
                'fuente': r.fuente,
            }
            for r in rows
        ]

    def _resumen_periodo(
        self,
        parcela_id: str,
        fecha_inicio: Optional[date],
        fecha_fin: Optional[date],
    ) -> dict:
        """
        Calcula estadísticas del período consultado.
        Siempre sobre todos los datos del período, no solo la página.
        """
        filtro_fechas = ''
        if fecha_inicio:
            filtro_fechas += ' AND fecha >= :fecha_inicio'
        if fecha_fin:
            filtro_fechas += ' AND fecha <= :fecha_fin'

        row = self.db.execute(
            text(f"""
                SELECT
                    COUNT(*)                        AS total_dias,
                    SUM(precipitacion_mm)           AS precip_total,
                    AVG(precipitacion_mm)           AS precip_promedio,
                    MAX(temperatura_max_c)          AS temp_maxima,
                    MIN(temperatura_min_c)          AS temp_minima,
                    AVG(temperatura_promedio_c)     AS temp_promedio,
                    AVG(humedad_relativa_porcentaje) AS humedad_promedio,
                    SUM(evapotranspiracion_mm)      AS et0_total,
                    COUNT(CASE WHEN precipitacion_mm > 0 THEN 1 END) AS dias_con_lluvia,
                    COUNT(CASE WHEN fuente = 'manual' THEN 1 END)    AS dias_manuales
                FROM datos_climaticos
                WHERE parcela_id = CAST(:parcela_id AS uuid)
                {filtro_fechas}
            """),
            {
                'parcela_id': parcela_id,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
            }
        ).fetchone()

        if not row or not row.total_dias:
            return {}

        return {
            'total_dias': int(row.total_dias),
            'dias_con_lluvia': int(row.dias_con_lluvia or 0),
            'dias_manuales': int(row.dias_manuales or 0),
            'precipitacion': {
                'total_mm': round(float(row.precip_total or 0), 1),
                'promedio_mm': round(float(row.precip_promedio or 0), 1),
            },
            'temperatura': {
                'maxima_c': round(float(row.temp_maxima), 1) if row.temp_maxima else None,
                'minima_c': round(float(row.temp_minima), 1) if row.temp_minima else None,
                'promedio_c': round(float(row.temp_promedio), 1) if row.temp_promedio else None,
            },
            'humedad_promedio': round(
                float(row.humedad_promedio), 1
            ) if row.humedad_promedio else None,
            'et0_total_mm': round(
                float(row.et0_total), 1
            ) if row.et0_total else None,
        }

    def _construir_filtros(
        self,
        fecha_inicio: Optional[date],
        fecha_fin: Optional[date],
        fuente: Optional[str],
    ) -> str:
        """
        Construye los filtros SQL dinámicamente según los parámetros.
        Solo agrega las condiciones que tienen valor.
        """
        filtros = ''
        if fecha_inicio:
            filtros += ' AND fecha >= :fecha_inicio'
        if fecha_fin:
            filtros += ' AND fecha <= :fecha_fin'
        if fuente:
            filtros += ' AND fuente = :fuente'
        return filtros