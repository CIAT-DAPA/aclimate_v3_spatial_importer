from setuptools import setup, find_packages

setup(
    name="aclimate_v3_spatial_importer",
    version='v3.0.1',
    author="dan3s",
    author_email="d.e.guzman@cgiar.com",
    description="Package to import spatial data into Geoserver",
    url="https://github.com/CIAT-DAPA/aclimate_v3_spatial_importer",
    download_url="https://github.com/CIAT-DAPA/aclimate_v3_spatial_importer",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    package_data={
        "aclimate_v3_spatial_importer": [
            "conf/**/*",
            "conf/*/*",    
        ]
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        "certifi==2025.4.26",
        "charset-normalizer==3.4.2",
        "gsconfig-py3==1.0.7",
        "idna==3.10",
        "requests==2.32.3",
        "urllib3==2.4.0",

    ]
)