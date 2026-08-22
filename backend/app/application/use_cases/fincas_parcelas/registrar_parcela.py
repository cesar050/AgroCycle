from app.domain.entities.parcela import Parcela
from app.domain.repositories.i_parcela_repository import IParcelaRepository
from app.domain.repositories.i_lote_repository import ILoteRepository
from app.infrastructure.external.topografia_service import (
    coordenadas_a_wkt,
    obtener_datos_topograficos_completos
)
from app.infrastructure.logging.logger import log_caso_de_uso


class RegistrarParcelaUseCase:
    """
    CU-GFP-003 Registrar Parcela.
    Registra una parcela con su geometria real, calcula superficie via
    PostGIS y obtiene topografia completa via OpenTopoData NASA SRTM.
    Genera una grilla inteligente de puntos dentro del poligono real
    segun el tamano de la parcela para maxima precision sin sensores.
    """

    def __init__(
        self,
        parcela_repository: IParcelaRepository,
        lote_repository: ILoteRepository
    ):
        self.parcela_repository = parcela_repository
        self.lote_repository = lote_repository

    @log_caso_de_uso('registrar_parcela')
    def ejecutar(
        self,
        lote_id: str,
        nombre: str,
        coordenadas: list,
        tipo_suelo_id: int = None,
        drenaje: str = None,
        acceso_riego: bool = False,
        tipo_riego: str = None,
        observaciones: str = None
    ) -> dict:
        """
        Registra una parcela con geometria real.
        Paso 1: Verifica que el lote exista.
        Paso 2: Convierte coordenadas a WKT para PostGIS.
        Paso 3: Calcula superficie en hectareas via PostGIS.
        Paso 4: Genera grilla inteligente y obtiene topografia NASA SRTM.
        Paso 5: Crea y persiste la parcela con todos sus datos.
        """
        # Paso 1: Verificar que el lote exista
        lote = self.lote_repository.buscar_por_id(lote_id)
        if not lote:
            raise ValueError("Lote no encontrado")

        if len(coordenadas) < 3:
            raise ValueError("El poligono debe tener al menos 3 puntos")

        # Paso 2: Convertir coordenadas a formato WKT para PostGIS
        geometria_wkt = coordenadas_a_wkt(coordenadas)

        # Paso 3: Calcular superficie real usando PostGIS
        # ST_Transform a UTM zona 17S para calculo metrico preciso en Ecuador
        superficie_ha = self.parcela_repository.calcular_superficie_ha(geometria_wkt)

        # Validar que la parcela este dentro del lote
        if not self.lote_repository.contiene_geometria(lote_id, geometria_wkt):
            raise ValueError(
                "La parcela debe estar dentro del poligono del lote. "
                "Verifica que las coordenadas esten correctas."
            )

        # Paso 4: Obtener topografia completa via OpenTopoData NASA SRTM
        # La grilla se adapta al tamano de la parcela automaticamente
        # Si falla no bloquea el registro — la parcela se guarda sin topografia
        datos_topografia = obtener_datos_topograficos_completos(
            coordenadas,
            superficie_ha
        )

        # Paso 5: Crear entidad de dominio
        nueva_parcela = Parcela(
            lote_id=lote_id,
            nombre=nombre.strip(),
            geometria_wkt=geometria_wkt,
            superficie_ha=superficie_ha,
            tipo_suelo_id=tipo_suelo_id,
            altitud_promedio_msnm=datos_topografia.get('altitud_promedio_msnm') if datos_topografia else None,
            altitud_minima_msnm=datos_topografia.get('altitud_minima_msnm') if datos_topografia else None,
            altitud_maxima_msnm=datos_topografia.get('altitud_maxima_msnm') if datos_topografia else None,
            pendiente_porcentaje=datos_topografia.get('pendiente_porcentaje') if datos_topografia else None,
            orientacion=datos_topografia.get('orientacion') if datos_topografia else None,
            drenaje=drenaje,
            acceso_riego=acceso_riego,
            tipo_riego=tipo_riego,
            observaciones=observaciones
        )

        parcela_guardada = self.parcela_repository.guardar(nueva_parcela)

        return {
            "id": parcela_guardada.id,
            "lote_id": parcela_guardada.lote_id,
            "nombre": parcela_guardada.nombre,
            "superficie_ha": parcela_guardada.superficie_ha,
            "altitud_promedio_msnm": parcela_guardada.altitud_promedio_msnm,
            "altitud_minima_msnm": parcela_guardada.altitud_minima_msnm,
            "altitud_maxima_msnm": parcela_guardada.altitud_maxima_msnm,
            "pendiente_porcentaje": parcela_guardada.pendiente_porcentaje,
            "orientacion": parcela_guardada.orientacion,
            "acceso_riego": parcela_guardada.acceso_riego,
            "activo": parcela_guardada.activo,
            "created_at": parcela_guardada.created_at.isoformat(),
            "num_puntos_consultados": datos_topografia.get('num_puntos_consultados') if datos_topografia else 0
        }