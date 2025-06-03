import os
import sys
import zipfile
import time
import shutil
from geoserver.catalog import Catalog
from geoserver.resource import Coverage
#import geoserver.util
from geoserver.support import DimensionInfo

# https://github.com/dimitri-justeau/gsconfig-py3


class GeoserverClient(object):

    url = ''
    user = ''
    pwd = ''
    catalog = None
    workspace = None
    workspace_name = ''

    def __init__(self, url, user, pwd):
        self.url = url
        self.user = user
        self.pwd = pwd
        self.catalog = None
        self.workspace = None
        self.workspace_name = ''

    def connect(self):
        try:
            self.catalog = Catalog(
                self.url, username=self.user, password=self.pwd)
            print("connected to Geoserver")
        except Exception as err:
            error = str(err).split()[50:61]
            print(" ".join(error))

    def get_workspace(self, name):
        if self.catalog:
            self.workspace = self.catalog.get_workspace(name)
            self.workspace_name = name
            print("Workspace found")
        else:
            print("Workspace not available")
            sys.exit()

    def get_store(self, store_name):
        if self.workspace:
            """
            store = self.catalog.get_store(store_name, self.workspace)
            if store:
                print("Store found")
                return store
            else:
                print("Store not found:", store_name)
                return None
            """
            try:
                store = self.catalog.get_store(store_name, self.workspace)
                return store
            except Exception as err:
                print("Store not found:", store_name)
                return None
        else:
            print("Workspace not found:", store_name)
            return None

    
    def zip_files(self, file: str, folder_properties: str, folder_tmp: str) -> str:
        """
        Crea un archivo ZIP con el archivo raster y las propiedades del mosaico
        """
        import logging
        from pathlib import Path
        
        logger = logging.getLogger(__name__)
        
        # Convertir todas las rutas a Path objects para mejor manejo
        file_path = Path(file).resolve()
        tmp_path = Path(folder_tmp).resolve()
        
        logger.info(f"Archivo origen: {file_path}")
        logger.info(f"Directorio temporal: {tmp_path}")
        
        # Obtener el nombre del archivo
        filename = file_path.name
        destination_path = tmp_path / filename
        
        logger.info(f"Destino planificado: {destination_path}")
        
        # SOLUCIÓN AL PROBLEMA: Verificar si son el mismo archivo antes de copiar
        try:
            # Si las rutas resueltas son diferentes, copiar el archivo
            if file_path != destination_path:
                logger.info(f"Copiando {file_path} a {destination_path}")
                shutil.copy2(str(file_path), str(destination_path))
            else:
                logger.info("El archivo ya está en la ubicación correcta, no es necesario copiarlo")
        except shutil.SameFileError:
            logger.warning(f"Origen y destino son el mismo archivo: {file}")
            # No hacer nada, continuar con el proceso
        except Exception as e:
            logger.error(f"Error copiando archivo: {e}")
            raise
        
        # Crear el archivo ZIP
        zip_path = tmp_path.parent / "mosaic.zip"
        
        try:
            with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Agregar todos los archivos del directorio temporal
                for root, dirs, files in os.walk(str(tmp_path)):
                    for file_name in files:
                        file_path_in_tmp = Path(root) / file_name
                        # Nombre del archivo en el ZIP (relativo al directorio tmp)
                        arcname = file_path_in_tmp.relative_to(tmp_path)
                        zipf.write(str(file_path_in_tmp), str(arcname))
                        logger.debug(f"Agregado al ZIP: {arcname}")
            
            logger.info(f"Archivo ZIP creado: {zip_path}")
            return str(zip_path)
            
        except Exception as e:
            logger.error(f"Error creando archivo ZIP: {e}")
            raise

    def create_mosaic(self, store_name, file, folder_properties, folder_tmp):
        output = self.zip_files(file, folder_properties, folder_tmp)
        print(output)
        self.catalog.create_imagemosaic(
            store_name, output, workspace=self.workspace)
        print(f"Mosaic store : {store_name} is created!")
        store = self.catalog.get_store(store_name, workspace=self.workspace)
        url = self.url + "workspaces/" + self.workspace_name + \
            "/coveragestores/" + store_name + "/coverages/" + store_name + ".xml"
        print(url)
        xml = self.catalog.get_xml(url)
        name = xml.find("name").text
        coverage = Coverage(self.catalog, store=store,
                            name=name, href=url, workspace=self.workspace)
        print("Get resource success")
        # defined coverage type for this store geotiff
        coverage.supported_formats = ["GEOTIFF"]
        # enable the time dimension
        timeInfo = DimensionInfo(name="time", enabled="true", presentation="LIST", resolution=None,
                                 units="ISO8601", unit_symbol=None)
        coverage.metadata = {
            "dirName": "f{store_name}_{store_name}", "time": timeInfo}
        self.catalog.save(coverage)
        # add style to the layer created
        # layer=cat.get_layer(store_name)
        # style=cat.get_style(style_name)
        # layer.default_style=style
        # cat.save(layer)
        print("Time Dimension is enabled")
        print("Done Successfully!")

    def update_mosaic(self, store_name, file, folder_properties, folder_tmp):
        output = self.zip_files(file, folder_properties, folder_tmp)
        self.catalog.harvest_uploadgranule(output, store_name)
        print("Mosaic updated")
    
    def delete_mosaic(self, store_name):
        store = self.get_store(store_name)
        if store:
            self.catalog.delete(store, recurse=True) 
            print("Mosaic deleted")
        else:
            print("Store not found:", store_name)

    def check(self, store):
        coverages = self.catalog.mosaic_coverages(store)
        granules = self.catalog.mosaic_granules(
            (coverages[b"coverages"][b"coverage"][0][b"name"]).decode("utf-8"), store)
        granules_count = len(granules[b"features"])
        print("granules", granules_count)

    def delete_folder_content(self, folder_path):
        list_dir = os.listdir(folder_path)
        for filename in list_dir:
            file_path = os.path.join(folder_path, filename)

            if os.path.isfile(file_path) or os.path.islink(file_path):
                print("deleting file:", file_path)
                os.unlink(file_path)

            elif os.path.isdir(file_path):
                print("deleting folder:", file_path)
                shutil.rmtree(file_path)


