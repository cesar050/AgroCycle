"""
CU-CLI-004 — Registrar evento climático manual.

Permite al agricultor registrar datos climáticos cuando:
- Open-Meteo no tiene datos para esa fecha
- El agricultor observó algo específico (lluvia fuerte, helada)
- Necesita corregir un dato incorrecto de la API

Los datos manuales tienen fuente='manual' para distinguirlos
de los datos descargados automáticamente de Open-Meteo.
"""
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.infrastructure.logging.logger import log_caso_de_uso
from app.infrastructure.transaction import transaccion_atomica


class RegistrarEventoManualUseCase:
    """
    Implementa CU-CLI-004.

    Responsabilidades:
    1. Verificar que la parcela pertenece al agricultor
    2. Verificar que no existe ya un dato para esa fecha
       (si existe, actualiza en lugar de duplicar)
    3. Guardar el dato climático con fuente='manual'
    """

    def __init__(self, db: Session):
        self.db = db

    @log_caso_de_uso('CU-CLI-004 Registrar Evento Climático Manual')
    def ejecutar(
        self,
        parcela_id: str,
        agricultor_id: str,
        fecha: date,
        precipitacion_mm: Optional[float] = None,
        temperatura_max_c: Optional[float] = None,
        temperatura_min_c: Optional[float] = None,
        temperatura_promedio_c: Optional[float] = None,
        humedad_relativa_porcentaje: Optional[float] = None,
        evapotranspiracion_mm: Optional[float] = None,
        velocidad_viento_km_h: Optional[float] = None,
    ) -> tuple:
        """
        Registra o actualiza un dato climático manual.

        Si ya existe un dato para esa fecha y parcela lo actualiza
        con los nuevos valores — no crea duplicados.

        Args:
            parcela_id: UUID de la parcela
            agricultor_id: UUID del usuario autenticado
            fecha: fecha del evento climático
            precipitacion_mm: lluvia registrada en mm
            temperatura_max_c: temperatura máxima del día
            temperatura_min_c: temperatura mínima del día
            temperatura_promedio_c: temperatura promedio
            humedad_relativa_porcentaje: humedad del aire
            evapotranspiracion_mm: ET0 estimada o medida
            velocidad_viento_km_h: velocidad del viento

        Returns:
            tuple (dict resultado, int código HTTP)
        """
        # 1. Verificar que al menos un campo climático fue enviado
        campos_climaticos = [
            precipitacion_mm, temperatura_max_c, temperatura_min_c,
            temperatura_promedio_c, humedad_relativa_porcentaje,
            evapotranspiracion_mm, velocidad_viento_km_h,
        ]
        if all(c is None for c in campos_climaticos):
            return {
                'error': 'Debe proporcionar al menos un dato climático.'
            }, 400

        # 2. Verificar que la parcela pertenece al agricultor
        parcela = self._verificar_parcela(parcela_id, agricultor_id)

        if not parcela:
            return {
                'error': 'Parcela no encontrada o no pertenece al agricultor.'
            }, 404

        # 3. Calcular temperatura promedio si no se proporcionó
        if temperatura_promedio_c is None and \
           temperatura_max_c is not None and \
           temperatura_min_c is not None:
            temperatura_promedio_c = round(
                (temperatura_max_c + temperatura_min_c) / 2, 1
            )

        # 4. Verificar si ya existe dato para esa fecha
        existe = self._existe_dato(parcela_id, fecha)

        try:
            with transaccion_atomica(self.db):
                if existe:
                    # Actualizar dato existente
                    self._actualizar_dato(
                        parcela_id, fecha,
                        precipitacion_mm, temperatura_max_c,
                        temperatura_min_c, temperatura_promedio_c,
                        humedad_relativa_porcentaje,
                        evapotranspiracion_mm, velocidad_viento_km_h,
                    )
                    accion = 'actualizado'
                else:
                    # Insertar nuevo dato manual
                    self._insertar_dato(
                        parcela_id, fecha,
                        precipitacion_mm, temperatura_max_c,
                        temperatura_min_c, temperatura_promedio_c,
                        humedad_relativa_porcentaje,
                        evapotranspiracion_mm, velocidad_viento_km_h,
                    )
                    accion = 'registrado'
        except Exception as e:
            return {
                'error': f'Error al registrar el evento: {str(e)}'
            }, 500

        return {
            'parcela_id': parcela_id,
            'parcela_nombre': parcela['nombre'],
            'fecha': str(fecha),
            'fuente': 'manual',
            'accion': accion,
            'datos_registrados': {
                'precipitacion_mm': precipitacion_mm,
                'temperatura_max_c': temperatura_max_c,
                'temperatura_min_c': temperatura_min_c,
                'temperatura_promedio_c': temperatura_promedio_c,
                'humedad_relativa_porcentaje': humedad_relativa_porcentaje,
                'evapotranspiracion_mm': evapotranspiracion_mm,
                'velocidad_viento_km_h': velocidad_viento_km_h,
            },
            'mensaje': f'Dato climático {accion} correctamente para el {fecha}.',
        }, 201 if accion == 'registrado' else 200

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

    def _existe_dato(self, parcela_id: str, fecha: date) -> bool:
        """Verifica si ya existe un dato climático para esa fecha."""
        row = self.db.execute(
            text("""
                SELECT id FROM datos_climaticos
                WHERE parcela_id = CAST(:parcela_id AS uuid)
                  AND fecha = :fecha
            """),
            {'parcela_id': parcela_id, 'fecha': fecha}
        ).fetchone()
        return row is not None

    def _insertar_dato(
        self, parcela_id, fecha, precipitacion_mm,
        temperatura_max_c, temperatura_min_c, temperatura_promedio_c,
        humedad_relativa_porcentaje, evapotranspiracion_mm,
        velocidad_viento_km_h,
    ) -> None:
        """Inserta un nuevo dato climático manual."""
        self.db.execute(
            text("""
                INSERT INTO datos_climaticos (
                    parcela_id, fecha, fuente,
                    precipitacion_mm,
                    temperatura_max_c, temperatura_min_c,
                    temperatura_promedio_c,
                    humedad_relativa_porcentaje,
                    evapotranspiracion_mm,
                    velocidad_viento_km_h
                ) VALUES (
                    CAST(:parcela_id AS uuid), :fecha, 'manual',
                    :precipitacion_mm,
                    :temperatura_max_c, :temperatura_min_c,
                    :temperatura_promedio_c,
                    :humedad_relativa_porcentaje,
                    :evapotranspiracion_mm,
                    :velocidad_viento_km_h
                )
            """),
            {
                'parcela_id': parcela_id,
                'fecha': fecha,
                'precipitacion_mm': precipitacion_mm or 0,
                'temperatura_max_c': temperatura_max_c,
                'temperatura_min_c': temperatura_min_c,
                'temperatura_promedio_c': temperatura_promedio_c,
                'humedad_relativa_porcentaje': humedad_relativa_porcentaje,
                'evapotranspiracion_mm': evapotranspiracion_mm,
                'velocidad_viento_km_h': velocidad_viento_km_h,
            }
        )

    def _actualizar_dato(
        self, parcela_id, fecha, precipitacion_mm,
        temperatura_max_c, temperatura_min_c, temperatura_promedio_c,
        humedad_relativa_porcentaje, evapotranspiracion_mm,
        velocidad_viento_km_h,
    ) -> None:
        """
        Actualiza un dato existente solo con los campos enviados.
        Los campos None no sobreescriben valores existentes.
        """
        self.db.execute(
            text("""
                UPDATE datos_climaticos SET
                    precipitacion_mm = COALESCE(
                        :precipitacion_mm, precipitacion_mm
                    ),
                    temperatura_max_c = COALESCE(
                        :temperatura_max_c, temperatura_max_c
                    ),
                    temperatura_min_c = COALESCE(
                        :temperatura_min_c, temperatura_min_c
                    ),
                    temperatura_promedio_c = COALESCE(
                        :temperatura_promedio_c, temperatura_promedio_c
                    ),
                    humedad_relativa_porcentaje = COALESCE(
                        :humedad_relativa_porcentaje,
                        humedad_relativa_porcentaje
                    ),
                    evapotranspiracion_mm = COALESCE(
                        :evapotranspiracion_mm, evapotranspiracion_mm
                    ),
                    velocidad_viento_km_h = COALESCE(
                        :velocidad_viento_km_h, velocidad_viento_km_h
                    ),
                    fuente = 'manual'
                WHERE parcela_id = CAST(:parcela_id AS uuid)
                  AND fecha = :fecha
            """),
            {
                'parcela_id': parcela_id,
                'fecha': fecha,
                'precipitacion_mm': precipitacion_mm,
                'temperatura_max_c': temperatura_max_c,
                'temperatura_min_c': temperatura_min_c,
                'temperatura_promedio_c': temperatura_promedio_c,
                'humedad_relativa_porcentaje': humedad_relativa_porcentaje,
                'evapotranspiracion_mm': evapotranspiracion_mm,
                'velocidad_viento_km_h': velocidad_viento_km_h,
            }
        )