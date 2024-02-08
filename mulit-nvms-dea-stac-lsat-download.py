#!/usr/bin/env python
"""
this script calls the script "nvms-wrs2-dea-stac-lsat_download.py" and applies it to a list of directories to process.    
Author: Grant Staben
Date: 01/12/2023
"""

# import the requried modules
import sys
import os
import argparse
import pdb
import pandas as pd
import csv


# command arguments 
def getCmdargs():

    p = argparse.ArgumentParser()

    p.add_argument("-d","--dirlist", help="read in the list of nvms directories to process")
        
    cmdargs = p.parse_args()
    
    # if there is no image list the script will terminate
    if cmdargs.dirlist is None:

        p.print_help()

        sys.exit()

    return cmdargs


def multiNVMS(dirlist):
    
    """
    call the 
    """
    
    # open the list of imagery and read it into memory
    df = pd.read_csv(dirlist,header=None)
    
    for index, row in df.iterrows():
                
        shp_dir = (str(row[0]))
        
              
        #print (fileN)
        print (shp_dir)         
 
        # call and run the vegetation index scripts 
        cmd = "python nvms-wrs2-dea-stac-lsat_download.py --shp_dir %s"% (shp_dir) 
            
        os.system(cmd)
        
def mainRoutine():
    
    # calls in the command arguments and multiNVMS function. 
    cmdargs = getCmdargs()
    
    multiNVMS(cmdargs.dirlist)

if __name__ == "__main__":
    mainRoutine()