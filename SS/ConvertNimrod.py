#  This file uses the nimrod.py module offered by CEDA to batch convert the full rain dataset (hopefully)...
import os
from NIMROD_Download_Convert_Python import nimrod
import arcpy
import glob
import multiprocessing
from functools import partial
from datetime import datetime


def main():
    startTime = datetime.now()
    print('start time = {0}'.format(startTime))
    ddir = os.path.abspath("D:/MetOfficeRadar_Data/Data/Extracted")
    edir = os.path.abspath("D:/MetOfficeRadar_Data/Data/format_tif")

    if not os.path.isdir(edir):
        os.mkdir(edir)

    paralellProcess(ddir, edir)

    finTime = datetime.now() - startTime
    print("script completed. \n"
          "Processing time = {0}".format(finTime))


def convert_dat_to_asc(outdir, file_list):
    coor_system = arcpy.SpatialReference("British National Grid")
    arcpy.env.cartographicCoordinateSystem = coor_system
    arcpy.env.outputCoordinateSystem = coor_system
    arcpy.env.compression = "LZ77"
    for name in file_list:

        fname = os.path.basename(name)
        fname = fname[:-3] + 'asc'

        # print(fname)
        print('coverting file to tif: {0}'.format(fname))

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

def paralellProcess(ras_folder, expdir):
    file_list = []

    for name in glob.glob(os.path.join(ras_folder, "*_1km-composite.dat")):
        file_list.append(name)


    n_feat = len(file_list)
    num_cores = multiprocessing.cpu_count() - 1
    print('n available cores  = {0}'.format(num_cores))
    n_split = int(n_feat/num_cores)

    list_split = [file_list[i:i + n_split] for i in range(0, len(file_list), n_split)]

    pool = multiprocessing.Pool(num_cores)

    print("Creating data frame of requested time frame... \n"
          "Time to go parallel... This may take a while")

    function = partial(convert_dat_to_asc, expdir)
    pool.map(function, list_split)

    pool.close()
    pool.join()


if __name__ == "__main__":
    main()

