# This script extracts all of the downloaded data to a new folder.

from tqdm import tqdm
import sys
import os
import glob
import shutil
import gzip
import nimrod
import arcpy
import multiprocessing
from functools import partial

from datetime import datetime
import time

# def main():
def main(ddirec, edirec):
    startTime = datetime.now()
    print('start time = {0}'.format(startTime))

    # ddir=os.path.abspath("D:/MetOfficeRadar_Data/UK_1km_Rain_Radar")
    # ddirec = os.path.abspath("D:/MetOfficeRadar_Data/Data/")
    # ddirec = os.path.abspath("D:/MetOfficeRadar_Data/Data/2_Day_Test_Ins")
    # edirec = os.path.abspath("D:/MetOfficeRadar_Data/Data/2_Day_Test_Out")
    # ddirec = os.path.abspath("C:/HG_Projects/SideProjects/Radar_Test_Data")
    # edirec = os.path.join(ddirec, 'Extracted2')


    if not os.path.isdir(edirec):
        os.mkdir(edirec)

    unzip_and_convert(ddirec, edirec)

    finTime = datetime.now() - startTime

    time.sleep(3)

    print("script completed. \n"
          "Processing time = {0}".format(finTime))



def unzip_and_convert(ddir, edir):

    print("extracting files begins...")

    all_files = glob.glob(os.path.join(ddir, "*_1km-composite.dat.gz.tar"))

    n = 365 #number of days per chunk

    all_files = [all_files[i:i + n] for i in range(0, len(all_files), n)]

    for chunk in tqdm(all_files):
        # print('extracting file: {0}'.format(name))
        for name in chunk:
            shutil.unpack_archive(filename=name, extract_dir=edir)

        for name in glob.glob(os.path.join(edir, "*_1km-composite.dat.gz")):
            # print('decompressing file: {0}'.format(name))

            inFile = gzip.GzipFile(name, 'rb')
            s = inFile.read()
            inFile.close()
            output = open(name[:-3], 'wb')
            output.write(s)
            output.close()

            # print("now delete intermediate file...")
            os.remove(name)
        paralellProcess(edir)


        # call convert
def convert_dat_to_asc(outdir, file_list):
    arcpy.SetLogHistory(False)
    coor_system = arcpy.SpatialReference("British National Grid")
    arcpy.env.cartographicCoordinateSystem = coor_system
    arcpy.env.outputCoordinateSystem = coor_system
    arcpy.env.compression = "LZ77"
    for name in file_list:

        fname = os.path.basename(name)
        fname = fname[:-3] + 'asc'

        # print(fname)
        # print('coverting file to tif: {0}'.format(fname))

        file_id = open(name, 'rb')

        a = nimrod.Nimrod(file_id)
        os.chdir(outdir)
        a.extract_asc(open(fname, 'w'))

        # print('defining Coord Ref System')
        asc_name = os.path.join(outdir, fname)
        saveras_path = os.path.join(outdir, fname[:-3] + 'tif')

        # load_ras = arcpy.Raster(asc_name)
        # load_ras.save(saveras_path)
        arcpy.ASCIIToRaster_conversion(asc_name, saveras_path, data_type="INTEGER")
        arcpy.DefineProjection_management(saveras_path, coor_system)

        os.remove(asc_name)
        os.remove(name)
    return()

def paralellProcess(ras_folder):
    sys.stdout = open(os.devnull, 'w')  # suppress printing
    file_list = []

    for name in glob.glob(os.path.join(ras_folder, "*_1km-composite.dat")):
        file_list.append(name)


    n_feat = len(file_list)
    num_cores = multiprocessing.cpu_count() - 1
    # print('n available cores  = {0}'.format(num_cores))
    n_split = int(n_feat/num_cores)

    list_split = [file_list[i:i + n_split] for i in range(0, len(file_list), n_split)]

    pool = multiprocessing.Pool(num_cores)

    # print("Creating data frame of requested time frame... \n"
    #       "Time to go parallel... This may take a while")

    function = partial(convert_dat_to_asc, ras_folder)
    pool.map(function, list_split)

    pool.close()
    pool.join()

    sys.stdout = sys.__stdout__  # enable printing

if __name__ == "__main__":
    # main()
    main(sys.argv[1],
         sys.argv[2])
