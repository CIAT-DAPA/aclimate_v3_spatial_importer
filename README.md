
# 📘 aclimate_v3_spatial_importer

## 🏷️ Version and tags
- Current version: `v3.0.1`
- Relevant tags: `raster`, `spatial data`, `geoserver`

---

## 📌 Introduction

Package developed to facilitate the upload of spatial data to the Geoserver platform in ImageMosaic format.

---

## ⚙️ Prerequisites

List of necessary tools to run the project:
- Python 3.10
- Geoserver

---

## ⚙️ Installation

```bash
pip install git+https://github.com/CIAT-DAPA/aclimate_v3_spatial_importer
```

To install a specific version:

```bash
pip install git+https://github.com/CIAT-DAPA/aclimate_v3_spatial_importer@v3.0.1
```

---

## 🔐 Environment Variable Configuration

Set environmental variables as follows:

- Windows:
```bash
set GEOSERVER_URL=http://your_geoserver/geoserver/rest/
set GEOSERVER_USER=your_user
set GEOSERVER_PASSWORD=your_password
```

- Linux:
```bash
export GEOSERVER_URL=http://your_geoserver/geoserver/rest/
export GEOSERVER_USER=your_user
export GEOSERVER_PASSWORD=your_password
```

---

## 🚀 Basic Usage

1. Upload raster files or delete store

```python
from aclimate_v3_spatial_importer import upload_image_mosaic

# Define required parameters
workspace = "test"
store = "test_store"
date_format = "yyyyMM"
data_dir = "./data/"
    
# Function to upload the image mosaic
upload_image_mosaic(workspace, store, data_dir, date_format)

#Functions to delete a store
delete_store(workspace, store)
```

> [!NOTE]  
>  You must change the paths to where your files are located.  
>  Required variables:
> - GEOSERVER_URL: Base URL of GeoServer (e.g., http://localhost:8080/geoserver/rest/)
> - GEOSERVER_USER: Username
> - GEOSERVER_PASSWORD: Password

---

## 🔄 CI/CD Pipeline Overview

### Workflow Architecture

Our GitHub Actions pipeline implements a three-stage deployment process:

```bash
Code Push → Test Stage → Merge Stage → Release Stage
```

---

## 🗂️ Project Structure

```bash
aclimate_v3_spatial_importer/
│
├── .github/
│   └── workflows/ # CI/CD pipeline configurations
├── src/
│   └── aclimate_v3_spatial_importer/
│       ├── conf/           # Date format for layers
│       ├── __init__.py     # Public interface
│       ├── importer.py     # Import to Geoserver function
│       └── tools.py        # gsconfig-py package functions
├── setup.py
└── requirements.txt        # Package dependencies
```
