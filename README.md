# Steps to install and set up the conda environment to run the DEA downloading scripts.

Conda is available in ArcGIS Pro. Open the python Command prompt – installed as part of ArcGIS Pro and create a new environment, cloning the arcgispro-py3 environment by entering the command below.

### conda create --clone arcgispro-py3 --name dea

Activate the new environment (dea) then install the packages using the commands below. 

### conda install rasterio
### conda install geopandas 
### pip install odc-stac
### pip install -U "aiobotocore[awscli,boto3]==1.3.3"
### pip install odc-apps-cloud
