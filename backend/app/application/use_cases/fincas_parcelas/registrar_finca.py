from app.domain.entities.finca import Finca
from app.infrastructure.external.topografia_service import coordenadas_a_wkt
from app.domain.repositories.i_finca_repository import IFincaRepository
from app.infrastructure.logging.logger import log_caso_de_uso


class RegistrarFincaUseCase:
    """
    CU-GFP-001: Registrar Finca.
    Un agricultor registra una nueva finca en el sistema.
    """

    def __init__(self, finca_repository: IFincaRepository):
        self.finca_repository = finca_repository

    @log_caso_de_uso('registrar_finca')
    def ejecutar(
        self,
        agricultor_id: str,
        nombre: str,
        coordenadas: list = None,
        provincia: str = None,
        canton: str = None,
        parroquia: str = None,
        sector: str = None,
        descripcion: str = None
    ) -> dict:
        """
        Registra una nueva finca para el agricultor.
        Paso 1: Verifica que no exista otra finca con el mismo nombre.
        Paso 2: Crea la entidad de dominio.
        Paso 3: Persiste mediante el repositorio.
        """
        # Paso 1: Validar nombre unico por agricultor
        if self.finca_repository.existe_nombre_para_agricultor(nombre, agricultor_id):
            raise ValueError(f"Ya tienes una finca registrada con el nombre '{nombre}'")

        # Paso 2: Crear entidad de dominio
        geometria_wkt = None
        superficie_ha = None
        if coordenadas and len(coordenadas) >= 3:
            geometria_wkt = coordenadas_a_wkt(coordenadas)
            superficie_ha = self.finca_repository.calcular_superficie_ha(geometria_wkt)
        
        nueva_finca = Finca(
            agricultor_id=agricultor_id,
            nombre=nombre.strip(),
            provincia=provincia,
            canton=canton,
            parroquia=parroquia,
            sector=sector,
            descripcion=descripcion,
            geometria_wkt=geometria_wkt,
            superficie_ha=superficie_ha
        )

        # Paso 3: Persistir
        finca_guardada = self.finca_repository.guardar(nueva_finca)

        return {
            "id": finca_guardada.id,
            "nombre": finca_guardada.nombre,
            "ubicacion": finca_guardada.nombre_completo_ubicacion(),
            "superficie_ha": finca_guardada.superficie_ha,
            "tiene_geometria": finca_guardada.tiene_geometria(),
            "activo": finca_guardada.activo,
            "created_at": finca_guardada.created_at.isoformat()
        }