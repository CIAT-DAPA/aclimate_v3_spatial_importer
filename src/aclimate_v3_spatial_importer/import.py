import os
import shutil
import logging
from typing import Optional
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
    geoserver_url: str,
    geo_user: Optional[str] = None,
    geo_pwd: Optional[str] = None
) -> None:
    """
    Sube un ImageMosaic a GeoServer
    
    Args:
        workspace: Nombre del workspace en GeoServer
        store: Nombre del store (mosaico)
        raster_dir: Directorio con los archivos raster
        date_format: Formato de fecha para los archivos (ej. 'yyyyMMdd')
        geoserver_url: URL del GeoServer
        geo_user: Usuario de GeoServer (opcional, toma de env vars por defecto)
        geo_pwd: Contraseña de GeoServer (opcional, toma de env vars por defecto)

    """
    # Validar formato de fecha
    if date_format not in VALID_DATE_FORMATS:
        raise ValueError(f"Formato de fecha inválido. Opciones válidas: {VALID_DATE_FORMATS}")
    
    # Obtener credenciales
    user = geo_user or os.getenv('GEO_USER')
    password = geo_pwd or os.getenv('GEO_PWD')
    
    if not user or not password:
        raise EnvironmentError("Credenciales de GeoServer no configuradas")
    
    # Configurar directorios
    base_dir = os.path.dirname(os.path.dirname(__file__))
    properties_dir = os.path.join(base_dir, "properties", date_format)
    print(properties_dir)
    tmp_dir = os.path.join(base_dir, "properties", "tmp")

    # Copiar el contenido de properties_dir a tmp_dir, reemplazando archivos existentes
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    shutil.copytree(properties_dir, tmp_dir)
    
    # Crear cliente
    #geo_url = "https://geo.aclimate.org/geoserver/rest/"
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
        mosaic_zip_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mosaic.zip")
        if os.path.exists(mosaic_zip_path):
            os.remove(mosaic_zip_path)


# base_dir = os.path.dirname(os.path.dirname(__file__))
# data_dir = os.path.join(base_dir, "data")
# upload_image_mosaic("test", "test_store", data_dir, "yyyyMM", "https://geo.aclimate.org/geoserver/rest/", "dguzman", "Mvu6ygSjQ#}hYW")