import os
from pathlib import Path
import uuid
import shutil
import logging
from .tools import GeoserverClient

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VALID_DATE_FORMATS = ['yyyy', 'yyyyMM', 'yyyyMMd', 'yyyyMMdd']

def upload_image_mosaic(
    workspace: str,
    store: str,
    raster_dir: str,
    date_format: str
) -> None:
    """
    Sube un ImageMosaic a GeoServer
    
    Args:
        workspace: Nombre del workspace en GeoServer
        store: Nombre del store (mosaico)
        raster_dir: Directorio con los archivos raster
        date_format: Formato de fecha para los archivos (ej. 'yyyyMMdd')
    """
    # Validar formato de fecha
    if date_format not in VALID_DATE_FORMATS:
        raise ValueError(f"Formato de fecha inválido. Opciones válidas: {VALID_DATE_FORMATS}")
    
    # Obtener credenciales de variables de entorno
    try:
        geoserver_url = os.environ['GEOSERVER_URL']
        user = os.environ['GEOSERVER_USER']
        password = os.environ['GEOSERVER_PASSWORD']
    except KeyError as e:
        raise EnvironmentError(
            f"Variable de entorno obligatoria no configurada: {e}. "
            "Debes configurar GEOSERVER_URL, GEOSERVER_USER y GEOSERVER_PASSWORD."
        ) from e
    
    # Configurar directorios usando rutas absolutas
    base_dir = Path(__file__).resolve().parent
    properties_dir = base_dir / "conf" / date_format
    
    #Crear directorio temporal con nombre único para evitar conflictos
    unique_id = uuid.uuid4().hex[:8]
    tmp_dir = base_dir / "conf" / f"tmp_{unique_id}"
    
    # Asegurarse de que raster_dir sea una ruta absoluta
    raster_dir = Path(raster_dir).resolve()

    # Copiar el contenido de properties_dir a tmp_dir, reemplazando archivos existentes
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    shutil.copytree(properties_dir, tmp_dir)
    
    # Crear cliente
    geoclient = GeoserverClient(geoserver_url, user, password)
    
    try:
        geoclient.connect()
        geoclient.get_workspace(workspace)
        
        # Obtener o crear store
        store_obj = geoclient.get_store(store)
        
        # Buscar archivos raster usando Path para mejor manejo de rutas
        raster_files = list(raster_dir.glob('*.tif')) + list(raster_dir.glob('*.tiff'))
        
        if not raster_files:
            raise FileNotFoundError(f"No se encontraron archivos raster en {raster_dir}")
        
        logger.info(f"Archivos encontrados: {[f.name for f in raster_files]}")
        
        for raster_path in raster_files:
            # Convertir a string para compatibilidad
            raster_path_str = str(raster_path)
            
            logger.info(f"Procesando archivo: {raster_path_str}")
            
            if not raster_path.exists():
                logger.warning(f"Archivo no encontrado: {raster_path_str}")
                continue
                
            if store_obj is None:
                logger.info("Creando nuevo mosaico")
                geoclient.create_mosaic(
                    store_name=store,
                    file=raster_path_str,
                    folder_properties=str(properties_dir),
                    folder_tmp=str(tmp_dir)
                )
                store_obj = geoclient.get_store(store)  # Actualizar referencia
                
            else:
                logger.info("Actualizando mosaico existente")
                geoclient.update_mosaic(
                    store_name=store_obj,
                    file=raster_path_str,
                    folder_properties=str(properties_dir),
                    folder_tmp=str(tmp_dir)
                )
                
    except Exception as e:
        logger.error(f"Error procesando {store}: {str(e)}")
        raise
    finally:
        # Limpiar directorios temporales
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
            

def delete_store(workspace, store_name):
    """
    Elimina un store de GeoServer
    """
    # Obtener credenciales de variables de entorno
    try:
        geoserver_url = os.environ['GEOSERVER_URL']
        user = os.environ['GEOSERVER_USER']
        password = os.environ['GEOSERVER_PASSWORD']
    except KeyError as e:
        raise EnvironmentError(
            f"Variable de entorno obligatoria no configurada: {e}. "
            "Debes configurar GEOSERVER_URL, GEOSERVER_USER y GEOSERVER_PASSWORD."
        ) from e
    
    # Crear cliente
    geoclient = GeoserverClient(geoserver_url, user, password)
    geoclient.connect()
    geoclient.get_workspace(workspace)    
    geoclient.delete_mosaic(store_name)