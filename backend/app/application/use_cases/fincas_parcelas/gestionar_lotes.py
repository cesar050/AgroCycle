from app.domain.entities.lote import Lote
from app.infrastructure.external.topografia_service import coordenadas_a_wkt
from app.domain.repositories.i_lote_repository import ILoteRepository
from app.domain.repositories.i_finca_repository import IFincaRepository
from app.infrastructure.logging.logger import log_caso_de_uso

class GestionarLotesUseCase:
    """
    CU-GFP-002: Gestionar lotes
    Un agricultor puede crear, listar y editar lotes dentro de sus fincas.
    """

    def __init__(
            self,
            lote_repository: ILoteRepository,
            finca_repository: IFincaRepository
    ):
        self.lote_repository = lote_repository
        self.finca_repository = finca_repository

    @log_caso_de_uso('registrar_lote')
    def registrar(
        self, 
        finca_id: str, 
        agricultor_id: str,
        nombre:str, 
        coordenadas: list = None,
        descripcion: str = None
    )-> dict:
        """
        Registra un nuevo lote dentro de una finca del agricultor
        Paso 1: Verifica que la finca exista y pertenezca al agricultor.
        Paso 2: Verifica que no exista otro lote con el mismo nombre.
        Paso 3: Crea y persiste el lote.
        """
        finca = self.finca_repository.buscar_por_id(finca_id)
        if not finca:
            raise ValueError("Finca no encontrada")
        geometria_wkt = None
        superficie_ha = None
        if coordenadas and len(coordenadas) >= 3:
            geometria_wkt = coordenadas_a_wkt(coordenadas)
            superficie_ha = self.lote_repository.calcular_superficie_ha(geometria_wkt)

        # Validar que el lote este dentro de la finca
        if finca.tiene_geometria():
            if not self.finca_repository.contiene_geometria(finca_id, geometria_wkt):
                raise ValueError(
                    "El lote debe estar dentro del poligono de la finca"
                )
        if not finca.es_del_agricultor(agricultor_id):
            raise PermissionError("No tienes permiso para agregar lotes a esta finca")
        if self.lote_repository.existe_nombre_en_finca(nombre, finca_id):
            raise ValueError(f"Ya existe un lote con el nombre '{nombre}' en esta finca")
        nuevo_lote = Lote(
            finca_id=finca_id,
            nombre=nombre.strip(),
            descripcion=descripcion,
            geometria_wkt=geometria_wkt,
            superficie_ha=superficie_ha
        )
        lote_guardado = self.lote_repository.guardar(nuevo_lote)

        return {
            "id":lote_guardado.id,
            "finca_id":lote_guardado.finca_id,
            "nombre":lote_guardado.nombre,
            "descripcion":lote_guardado.descripcion,
            "superficie_ha": lote_guardado.superficie_ha,
            "tiene_geometria": lote_guardado.tiene_geometria(),
            "activo":lote_guardado.activo,
            "created_at":lote_guardado.created_at.isoformat()
        }
    @log_caso_de_uso('listar_lotes')
    def listar(self, finca_id:str, agricultor_id:str)->list:
        """
        Lista todos los lotes activos de una finca del agricultor.
        """

        finca = self.finca_repository.buscar_por_id(finca_id)
        if not finca:
            raise ValueError("Finca no encontrada")
        if not finca.es_del_agricultor(agricultor_id):
            raise PermissionError("No tienes permiso para ver los lotes de esta finca")
        lotes = self.lote_repository.listar_por_finca(finca_id)
        return[
            {
            "id":l.id,
            "finca_id":l.finca_id,
            "nombre":l.nombre,
            "descripcion":l.descripcion,
            "activo":l.activo,
            "created_at":l.created_at.isoformat() if l.created_at else None
            }
            for l in lotes
        ]
