import os
import sys
import zipfile
from pathlib import Path
import shutil
from tqdm import tqdm
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
        Crea un archivo ZIP con el archivo raster o directorio y las propiedades del mosaico,
        colocando todos los archivos en la raíz del ZIP.
        """
        
        file_path = Path(file).resolve()
        tmp_path = Path(folder_tmp).resolve()
        content_path = tmp_path / "content"  # Carpeta temporal para el contenido plano
        content_path.mkdir(parents=True, exist_ok=True)
        
        # 1. Copiar archivos raster (solo los archivos, no la estructura de directorios)
        if file_path.is_dir():
            # Copiar todos los archivos del directorio a la carpeta content (sin subdirectorios)
            for item in file_path.iterdir():
                if item.is_file():
                    shutil.copy2(item, content_path / item.name)
        else:
            # Copiar archivo individual
            shutil.copy2(file_path, content_path / file_path.name)
        
        # 2. Copiar archivos de propiedades directamente a content_path
        properties_path = Path(folder_properties).resolve()
        if properties_path.is_dir():
            for prop_file in properties_path.iterdir():
                if prop_file.is_file():
                    shutil.copy2(prop_file, content_path / prop_file.name)
        
        # 3. Crear ZIP con todos los archivos en la raíz
        zip_path = tmp_path.parent / "mosaic.zip"
        
        # Listar todos los archivos en content_path
        all_files = list(content_path.iterdir())
        
        # Comprimir con barra de progreso (todos los archivos en raíz)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_in_content in tqdm(all_files, desc="Compressing files", unit="file"):
                if file_in_content.is_file():
                    # Usar solo el nombre del archivo (sin rutas) para arcname
                    zipf.write(file_in_content, file_in_content.name)
        
        return str(zip_path)

    def create_mosaic(self, store_name, file, folder_properties, folder_tmp):
        output = self.zip_files(file, folder_properties, folder_tmp)
        print(f"Working...")
        self.catalog.create_imagemosaic(
            store_name, output, workspace=self.workspace)
        print(f"Mosaic store : {store_name} is created!")
        store = self.catalog.get_store(store_name, workspace=self.workspace)
        url = self.url + "workspaces/" + self.workspace_name + \
            "/coveragestores/" + store_name + "/coverages/" + store_name + ".xml"
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


