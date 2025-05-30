import os
from pathlib import Path
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
    date_format: str,
    replace: bool = False
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
    """
        geoserver_url: URL del GeoServer
        geo_user: Usuario de GeoServer
        geo_pwd: Contraseña de GeoServer
    """
    try:
        geoserver_url = os.environ['GEOSERVER_URL']
        user = os.environ['GEOSERVER_USER']
        password = os.environ['GEOSERVER_PASSWORD']
    except KeyError as e:
        raise EnvironmentError(
            f"Variable de entorno obligatoria no configurada: {e}. "
            "Debes configurar GEOSERVER_URL, GEOSERVER_USER y GEOSERVER_PASSWORD."
        ) from e
    
    # Configurar directorios
    base_dir = Path(__file__).resolve().parent
    properties_dir = base_dir / "conf" / date_format
    tmp_dir = base_dir / "conf" / "tmp"

    # Copiar el contenido de properties_dir a tmp_dir, reemplazando archivos existentes
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    shutil.copytree(properties_dir, tmp_dir)
    
    # Crear cliente
    geoclient = GeoserverClient(geoserver_url, user, password)
    
    try:
        geoclient.connect()
        geoclient.get_workspace(workspace)
        
        # Obtener o crear store
        store_obj = geoclient.get_store(store)
        raster_files = [os.path.join(raster_dir, f) for f in os.listdir(raster_dir)
                        if f.endswith(('.tif', '.tiff'))]
        
        if not raster_files:
            raise FileNotFoundError(f"No se encontraron archivos raster en {raster_dir}")
        
        for raster_path in raster_files:
            if not os.path.exists(raster_path):
                continue
                
            if store_obj is None:
                logger.info("Creando nuevo mosaico")
                geoclient.create_mosaic(
                    store_name=store,
                    file=raster_path,
                    folder_properties=properties_dir,
                    folder_tmp=tmp_dir
                )
                store_obj = geoclient.get_store(store)  # Actualizar referencia
            # Si el store ya existe y replace es True, reemplazar el mosaico
            elif store_obj is not None and replace:
                logger.info("Reemplazando mosaico existente")
                geoclient.replace_mosaic(
                    store_name=store,
                    file=raster_path,
                    folder_properties=properties_dir,
                    folder_tmp=tmp_dir
                )
                store_obj = geoclient.get_store(store)  # Actualizar referencia

            else:
                logger.info("Actualizando mosaico existente")
                geoclient.update_mosaic(
                    store=store_obj,
                    file=raster_path,
                    folder_properties=properties_dir,
                    folder_tmp=tmp_dir
                )
                
    except Exception as e:
        logger.error(f"Error procesando {store}: {str(e)}")
        raise
    finally:
        # Limpiar directorios temporales
        mosaic_zip_path = Path(__file__).resolve().parent.parent.parent / "mosaic.zip"
        if os.path.exists(mosaic_zip_path):
            os.remove(mosaic_zip_path)
