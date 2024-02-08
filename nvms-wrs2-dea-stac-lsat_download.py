#!/usr/bin/env python
"""
This script downloads Landsat imagery stored in the Digital Earth Australia Amazon Web Service’s S3 Service. The Landsat imagery downloaded has been used to produce a vector layer (shapefile) identifying possible areas of vegetation change. 

The shapefile has been produced by the QLD Governments Remote Sensing Centre and the shapefile file name contains the Landsat Path/Row and the pre and post Landsat image dates used in the analysis. This script takes the path/row and pre and post dates from the shapefile name and searches the DEA STAC catalogue and downloads the nbart product for the relevant imagery, producing a composite image ready for analysis. The script creates an individual folder for each Landsat image which is stored along with the change detection shapfile. The seven 30m multispectral Landsat bands are used to make the composite while the 15m panchromatic band is retained to assist in visual analysis. Further information on the nbart product can be found here: https://cmi.ga.gov.au/data-products/dea/400/dea-surface-reflectance-nbart-landsat-8-oli-tirs 

Note: this script references the shapefile "WRS2_AU_centroid_buff50m.shp" to obtain the centre coordinates for each path/row.

Author: Grant Staben
email: grant.staben@dcceew.gov.au
Date: 01/12/2023
Version: 1.0



###############################################################################################

MIT License

Copyright (c) 2023 Grant Staben

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

###############################################################################################

Parameters: 
-----------

shp_dir : str 
              is a string containing the name of the directory containing the QLD landsat EDS shapefile.



"""


import argparse
import urllib.request, json
import pandas as pd
import geopandas as gpd
import xarray as xr
import odc.aws
from pprint import pprint
from datacube.testutils.io import rio_slurp_xarray
import glob, os
import rasterio
import shutil
import pathlib

# odc-stac library downloads DEA datasets stored in AWS
# when external to AWS (like outside DEA sandbox), AWS signed requests must be disabled
os.environ['AWS_NO_SIGN_REQUEST'] = 'YES'



def getCmdargs():
    """
    Command line arguments 
    """
    p = argparse.ArgumentParser()

    p.add_argument("--shp_dir", help="path to directory where the NVMS change shapefile is stored")
    
    cmdargs = p.parse_args()
    
    if cmdargs.shp_dir is None:

        p.print_help()

        sys.exit()

    return cmdargs


def download(data):
    
    # if true dowload the slected bands
    stac_item = data['features'][0]
    urls = [asset['href'] for asset in stac_item['assets'].values()]

    # now we select only the file with the text 'band' in them as these are the surface reflectance bansds we want 
    # and download them to create the composite image
    for url in urls:
        if 'band' in url:
            odc.aws.s3_download(url)

def stackBands():
    
    file_list = []
    
    for file in glob.glob("*.tif"):
        print (file)
        # check for the pancromatic band8 (15m spatial resolution) and do not add it to the list
        if 'band08' in file:
            pass 
        else:
            file_list.append(file)
    
    comp_file_name = file_list[0][:-10] + 'comp.tif'
    
    
    band_list = file_list

    # Read metadata of first file
    with rasterio.open(band_list[0]) as src0:
        meta = src0.meta

    # Update meta to reflect the number of layers
    meta.update(count= len(band_list))

    # Read each layer and write it to stack
    with rasterio.open(comp_file_name, 'w', **meta, compress='lzw') as dst:
        for id, layer in enumerate(band_list, start=1):
            with rasterio.open(layer) as src1:
                dst.write_band(id, src1.read(1))
                
    for file in band_list:
        os.remove(file) 
    print("Individual bands have been deleted")               

                
def makeTempDir(path,tempDir):
    # make a temp dir to save the individual band results 
          
    check_if_dir_exists = os.path.isdir(tempDir)
    print (check_if_dir_exists)
    if check_if_dir_exists == True:
        print (tempDir)
        shutil.rmtree(tempDir)
        
    os.mkdir(path)
    print ("made a new dir")      

def mainRoutine():
                   
    homeDir = os.getcwd()
    
    cmdargs = getCmdargs()              
                   
    nvms_shp_dir = cmdargs.shp_dir
    
    os.chdir(nvms_shp_dir)
    print (os.getcwd())
    
    # read in the change detection shapefile and extract out the path/row and pre and post image dates
    shp_name = glob.glob("*.shp")
    file_name = str(shp_name).strip("'[]'")
    
    path = file_name[8:11]
    row = file_name[12:15]
    PathRow = int(path+row)
    
    pre_img = pd.to_datetime(file_name[17:25]).date() # extract pre image date
    post_img = pd.to_datetime(file_name[25:33]).date() # extract post image date
    dates = []
    dates.append(pre_img)
    dates.append(post_img)
    print (dates)
    
    # because bounding box data can cover areas into a different target path/row we get the centroid of the path/row we are working with and use it to define the bbox variable needed to produce the STAC query.
    
    # open the wrs2 shapfile which defines the centroid of each path/row a extract out the relevent bbox for the STAC query
    wrs2 = gpd.read_file("N:/nvms/code/dea_lsat/WRS2_AU_centroid_buff50m.shp")
    
    path_row = wrs2[(wrs2['WRSPR'] == PathRow)]
    bbox = list(path_row.total_bounds)
    print (bbox)
       
    for date in dates:
               
        # Query the stac catalouge to identify if the image date is Landsat 8 sensor
        product = 'ga_ls8c_ard_3' # product to look for
        # query the dea-stac catalouge
        root_url = 'https://explorer.sandbox.dea.ga.gov.au/stac'
        stac_url = f'{root_url}/search?collection={product}&time={date}&bbox={str(bbox).replace(" ", "")}&limit=1'
                
        with urllib.request.urlopen(stac_url) as url:
            data = json.loads(url.read().decode())
        pprint(data, depth=1)
        
        # check to see if there is any landsat 8 imagery available for this date, if true download and stack the bands to produce a composite image, if False check for Landsat 9 imagery. 
        if data['numberReturned']==1:
            
            image_dir =  product + '_' + str(date) + '_imagery'
            
            os.makedirs(image_dir)
            os.chdir(image_dir)
            print (os.getcwd())
            
            # run the function to download the landsat bands
            download(data)
            # run the function to create a composite image 
            stackBands()
            
            os.chdir("..")
            
        # check to see if there is any landsat 9 imagery available for this date, if true download and stack the bands to produce a composite image
        elif data['numberReturned']==0:
            
            # Query the stac catalouge to identify if the image date is Landsat 9 sensor
            product = 'ga_ls9c_ard_3' # product to look for
            # query the dea-stac catalouge
            root_url = 'https://explorer.sandbox.dea.ga.gov.au/stac'
            stac_url = f'{root_url}/search?collection={product}&time={date}&bbox={str(bbox).replace(" ", "")}&limit=1'
            print(stac_url)
            
            with urllib.request.urlopen(stac_url) as url:
                data = json.loads(url.read().decode())
            pprint(data, depth=1)
                
            # if true dowload the slected bands
            if data['numberReturned']==1:
                
                image_dir =  product + '_' + str(date) + '_imagery'
                os.makedirs(image_dir)
                os.chdir(image_dir)
            
                print (os.getcwd())
                # run the function to download the landsat bands
                download(data)
                # run the function to create a composite image 
                stackBands()
                
                os.chdir("..")
        # if there are no Landsat 8 or 9 imagery associated for a date this message will be printed. 
        else: print("There is no Landsat 8 or 9 imagery available for this date")
        
    os.chdir(homeDir)
    
if __name__ == "__main__":
    mainRoutine()     