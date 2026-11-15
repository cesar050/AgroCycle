"""
Implementacion PostgreSQL del repositorio de consultas agregadas del
modulo Mapa. El SQL aqui es el mismo que antes vivia directo en las
rutas de interfaces/ — se movio tal cual detras de IMapaQueryRepository
para que las rutas dejen de hablarle a la base de datos directamente.
"""
import json
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.domain.repositories.i_mapa_query_repository import IMapaQueryRepository


class PgMapaQueryRepository(IMapaQueryRepository):

    def __init__(self, db: Session):
        self.db = db

    def obtener_finca_con_geojson(self, finca_id: str) -> Optional[dict]:
        row = self.db.execute(text("""
            SELECT
                f.id, f.nombre, f.superficie_ha,
                f.provincia, f.canton, f.parroquia, f.sector,
                ST_AsGeoJSON(f.geometria) AS geojson
            FROM fincas f
            WHERE f.id = CAST(:finca_id AS uuid)
              AND f.activo = TRUE
        """), {'finca_id': finca_id}).fetchone()

        if not row:
            return None

        return {
            'id': str(row.id),
            'nombre': row.nombre,
            'superficie_ha': float(row.superficie_ha or 0),
            'provincia': row.provincia,
            'canton': row.canton,
            'parroquia': row.parroquia,
            'sector': row.sector,
            'geojson': json.loads(row.geojson) if row.geojson else None,
        }

    def listar_lotes_con_geojson(self, finca_id: str) -> List[dict]:
        rows = self.db.execute(text("""
            SELECT
                l.id, l.nombre, l.superficie_ha,
                ST_AsGeoJSON(l.geometria) AS geojson
            FROM lotes l
            WHERE l.finca_id = CAST(:finca_id AS uuid)
              AND l.activo = TRUE
            ORDER BY l.nombre
        """), {'finca_id': finca_id}).fetchall()

        return [
            {
                'id': str(r.id),
                'nombre': r.nombre,
                'superficie_ha': float(r.superficie_ha or 0),
                'geojson': json.loads(r.geojson) if r.geojson else None,
            }
            for r in rows
        ]

    def listar_parcelas_con_estado(self, finca_id: str) -> List[dict]:
        rows = self.db.execute(text("""
            SELECT
                p.id,
                p.nombre,
                p.superficie_ha,
                p.altitud_promedio_msnm,
                p.pendiente_porcentaje,
                p.orientacion,
                l.id AS lote_id,
                COALESCE(tp.estado_fenologico, 'pre_siembra') AS estado_fenologico,
                COALESCE(tp.avance_ciclo_porcentaje, 0)       AS avance_ciclo,
                COALESCE(tp.produccion_real_qq, 0)            AS produccion_real,
                COALESCE(e.valor_qq_ha, 0)                    AS estimacion_qq_ha,
                ST_AsGeoJSON(p.geometria) AS geojson
            FROM parcelas p
            JOIN lotes l ON p.lote_id = l.id
            LEFT JOIN temporada_parcelas tp
                ON tp.parcela_id = p.id AND tp.activo = TRUE
            LEFT JOIN LATERAL (
                SELECT ep.valor_qq_ha
                FROM estimaciones_produccion ep
                WHERE ep.temporada_parcela_id = tp.id
                ORDER BY ep.fecha_generacion DESC
                LIMIT 1
            ) e ON TRUE
            WHERE l.finca_id = CAST(:finca_id AS uuid)
              AND p.activo = TRUE
            ORDER BY l.nombre, p.nombre
        """), {'finca_id': finca_id}).fetchall()

        return [
            {
                'id': str(r.id),
                'nombre': r.nombre,
                'superficie_ha': float(r.superficie_ha or 0),
                'altitud_msnm': float(r.altitud_promedio_msnm or 0),
                'pendiente': float(r.pendiente_porcentaje or 0),
                'orientacion': r.orientacion,
                'lote_id': str(r.lote_id),
                'estado_fenologico': r.estado_fenologico,
                'avance_ciclo': float(r.avance_ciclo or 0),
                'produccion_real': float(r.produccion_real or 0),
                'estimacion_qq_ha': float(r.estimacion_qq_ha or 0),
                'geojson': json.loads(r.geojson) if r.geojson else None,
            }
            for r in rows
        ]

    def listar_parcelas_geojson_simple(self, finca_id: str) -> List[dict]:
        rows = self.db.execute(text("""
            SELECT
                p.id,
                p.nombre,
                p.superficie_ha,
                p.altitud_promedio_msnm,
                p.pendiente_porcentaje,
                p.orientacion,
                tp.estado_fenologico,
                ST_AsGeoJSON(p.geometria) as geojson
            FROM parcelas p
            JOIN lotes l ON p.lote_id = l.id
            JOIN fincas f ON l.finca_id = f.id
            LEFT JOIN temporada_parcelas tp ON tp.parcela_id = p.id
                AND tp.activo = TRUE
            WHERE f.id = CAST(:finca_id AS uuid)
              AND p.activo = TRUE
            ORDER BY p.nombre
        """), {'finca_id': finca_id}).fetchall()

        return [
            {
                'id': str(r.id),
                'nombre': r.nombre,
                'superficie_ha': float(r.superficie_ha or 0),
                'altitud_msnm': float(r.altitud_promedio_msnm or 0),
                'pendiente': float(r.pendiente_porcentaje or 0),
                'orientacion': r.orientacion,
                'estado_fenologico': r.estado_fenologico,
                'geojson': json.loads(r.geojson) if r.geojson else None,
            }
            for r in rows
        ]

    def obtener_geometria_parcela(self, parcela_id: str) -> Optional[dict]:
        row = self.db.execute(text("""
            SELECT id, nombre, superficie_ha, ST_AsGeoJSON(geometria) as geojson
            FROM parcelas
            WHERE id = CAST(:id AS uuid)
        """), {"id": parcela_id}).fetchone()

        if not row:
            return None

        return {
            'id': str(row.id),
            'nombre': row.nombre,
            'superficie_ha': float(row.superficie_ha or 0),
            'geojson': json.loads(row.geojson) if row.geojson else None,
        }

    def listar_centroides_parcelas(self, finca_id: str) -> List[dict]:
        rows = self.db.execute(text("""
            SELECT
                p.id,
                p.nombre,
                p.tipo_suelo_id,
                ST_Y(ST_Centroid(p.geometria)) AS lat,
                ST_X(ST_Centroid(p.geometria)) AS lng
            FROM parcelas p
            JOIN lotes l ON p.lote_id = l.id
            WHERE l.finca_id = CAST(:finca_id AS uuid)
              AND p.activo = TRUE
        """), {'finca_id': finca_id}).fetchall()

        return [
            {
                'id': str(r.id),
                'nombre': r.nombre,
                'tipo_suelo_id': r.tipo_suelo_id,
                'lat': r.lat,
                'lng': r.lng,
            }
            for r in rows
        ]

    def obtener_bbox_parcelas(self, finca_id: str) -> Optional[tuple]:
        row = self.db.execute(text("""
            WITH ext AS (
                SELECT ST_Extent(p.geometria) AS bbox
                FROM parcelas p
                JOIN lotes l ON p.lote_id = l.id
                WHERE l.finca_id = CAST(:finca_id AS uuid)
                  AND p.activo = TRUE
            )
            SELECT
                ST_XMin(bbox) AS min_lng,
                ST_YMin(bbox) AS min_lat,
                ST_XMax(bbox) AS max_lng,
                ST_YMax(bbox) AS max_lat
            FROM ext
        """), {'finca_id': finca_id}).fetchone()

        if not row or row.min_lng is None:
            return None

        return (row.min_lng, row.min_lat, row.max_lng, row.max_lat)
