# This script extracts all of the downloaded data to a new folder.

from tqdm import tqdm
import sys
import os
import glob
import shutil
import gzip
import nimrod
# import arcpy
import multiprocessing
from functools import partial

import rasterio
from rasterio.crs import CRS

import numpy as np

from datetime import datetime
import time

def main():
# def main(ddirec, edirec):
    startTime = datetime.now()
    print('start time = {0}'.format(startTime))


    ddirec = os.path.abspath('D:/MetOfficeRadar_Data/UK_1km_Rain_Radar_Raw')
    edirec = os.path.abspath('D:/MetOfficeRadar_Data/UK_1km_Rain_Radar_Processed')



    # ddirec = os.path.abspath("D:/MetOfficeRadar_Data/Data/10_Day_Test_Ins")
    # edirec = os.path.abspath("D:/MetOfficeRadar_Data/Data/10_Day_Test_Out_rast")
    # ddirec = os.path.abspath("D:/MetOfficeRadar_Data/Data/2_Day_Test_Ins")
    # edirec = os.path.abspath("D:/MetOfficeRadar_Data/Data/2_Day_Test_Out_rast")



    if not os.path.isdir(edirec):
        os.mkdir(edirec)


    fileList = glob.glob(os.path.join(ddirec, "*_1km-composite.dat.gz.tar"))

    # fileList = checklist(all_files, edirec)

    unzip_and_convert(ddirec, edirec, fileList)

    finTime = datetime.now() - startTime

    time.sleep(3)

    print("script completed. \n"
          "Processing time = {0}".format(finTime))

# def checklist(file_List, edir):
#     print("checking to see if Raster(s) already exists... \n"
#           "If so - remove from processing list.")
#     print(len(file_List))
#     skip_list = glob.glob(os.path.join(edir, "*_1km-composite.tif"))
#     skip_list = [int(x[-30:-22]) for x in skip_list]
#     skip_list = list(dict.fromkeys(skip_list))
#     for x in file_List:
#         checkVal = int(x[-33:-25])
#         if checkVal in skip_list:
#             print(checkVal)
#             file_List.remove(x)
#     print(len(file_List))
#     print(file_List[0:10])
#     return file_List

def unzip_and_convert(ddir, edir, file_list):

    print("extracting files begins...")

    n = 100  # number of days per chunk

    all_files = [file_list[i:i + n] for i in range(0, len(file_list), n)]
    print(file_list)

    time.sleep(1)
    for chunk in tqdm(all_files):
        # print('extracting file: {0}'.format(name))
        for name in chunk:
            try:
                shutil.unpack_archive(filename=name, extract_dir=edir)
            except shutil.ReadError:
                pass
        work_chunk = glob.glob(os.path.join(edir, "*_1km-composite.dat.gz"))
        if len(work_chunk) < 1:
            continue
        for name in work_chunk:
            # print('decompressing file: {0}'.format(name))
            try:
                inFile = gzip.GzipFile(name, 'rb')
                s = inFile.read()
                inFile.close()
                output = open(name[:-3], 'wb')
                output.write(s)
                output.close()
                os.remove(name)
            except Exception:  #  so far errors have included: OS.Error and zlib.error: Error -3 while decompressing data: invalid block type
                pass
            # print("now delete intermediate file...")
            try:
                if 'output' in locals():
                    output.close()
                    os.remove(name)
            except Exception:
                pass

        paralellProcess(edir)


        # call convert
def convert_dat_to_asc(outdir, file_list):
    # arcpy.SetLogHistory(False)
    epsg = str(27700)
    # coor_system = arcpy.SpatialReference("British National Grid")
    # arcpy.env.cartographicCoordinateSystem = coor_system
    # arcpy.env.outputCoordinateSystem = coor_system
    # arcpy.env.compression = "LZ77"
    for name in file_list:

        fname = os.path.basename(name)
        fname = fname[:-3] + 'asc'

        asc_name = os.path.join(outdir, fname)
        saveras_path = os.path.join(outdir, fname[:-3] + 'tif')

        if os.path.exists(saveras_path):
            if os.path.exists(asc_name):
                os.remove(asc_name)
            if os.path.exists(name):
                os.remove(name)
        else:
            try:
                file_id = open(name, 'rb')

                a = nimrod.Nimrod(file_id)
                os.chdir(outdir)
                a.extract_asc(open(fname, 'w'))

                # print('defining Coord Ref System')

                #with rasterio
                src = rasterio.open(asc_name)
                array = src.read(1)

                array = array.astype(np.int16)
                out_meta = src.meta.copy()

                out_meta.update(
                    {"driver": "GTiff", "count": 1, "dtype": rasterio.int16,
                     "crs": CRS.from_epsg(epsg), "compress": "lzw"})

                # print("exporting output raster")

                with rasterio.open(saveras_path, "w", **out_meta) as dest:
                    dest.write(array.astype(rasterio.int16), 1)

                src.close()
                # with arcpy
                # arcpy.ASCIIToRaster_conversion(asc_name, saveras_path, data_type="INTEGER")
                # arcpy.DefineProjection_management(saveras_path, coor_system)

                if os.path.exists(asc_name):
                    os.remove(asc_name)
                if os.path.exists(name):
                    os.remove(name)

            except Exception as e: # This is a vague error catch but if there is any issue with the above - rather it continues
                print(e)
                if 'src' in locals():
                    src.close()
                if 'file_id' in locals():
                    file_id.close()

                if os.path.exists(asc_name):
                    os.remove(asc_name)
                if os.path.exists(name):
                    os.remove(name)
        #  I removed the return command - not sure if that was causing any issues?


def paralellProcess(ras_folder):
    # sys.stdout = open(os.devnull, 'w')  # suppress printing
    file_list = []

    for name in glob.glob(os.path.join(ras_folder, "*_1km-composite.dat")):
        file_list.append(name)


    n_feat = len(file_list)
    num_cores = multiprocessing.cpu_count() - 3  # lowered number of cores to see if that helps...
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

    # sys.stdout = sys.__stdout__  # enable printing

if __name__ == "__main__":
    main()
    # main(sys.argv[1],
    #      sys.argv[2])
