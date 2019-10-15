# Script builds rainfall time series from Nimrod MetOffice rainfall data. Data must already be converted into an
# ESRI readable Raster Format.

import os
import arcpy
import multiprocessing
from arcpy import env
import sys
import glob
import pandas as pd
# from tqdm import tqdm # JUST FOR TESTING...
from functools import partial
from datetime import datetime
import shutil

# Check out the ArcGIS Spatial Analyst extension license
arcpy.env.cartographicCoordinateSystem = arcpy.SpatialReference("British National Grid")
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("British National Grid")
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")


# Data_folder = os.path.abspath("Y:/shared_data/01_Radar/01_Converted_15_minutes_data/Exports_2012_2018")
Data_folder = os.path.abspath("D:/MetOfficeRadar_Data/UK_1km_Rain_Radar_Processed")
bound_shp = os.path.abspath("C:/HG_Projects/Event_Sep_R/Catchment_Area/Out_Catchments/Bud_Brook_Catch.shp")

Export_folder = os.path.abspath("C:/HG_Projects/Event_Sep_R/Radar_Rain_Exports")



area_field_name = ""

# start_date = '201908050000'
# end_date = '201908162355'

start_date = '200907090000'
end_date = '201904040900'

timestep = '15Min'   # set the desired time step for rainfall time series minimum of '5Min'. other options: 'D' for daily,
                     # 'W' for weekly. for more info look up pandas resample.

scratch = r"in_memory"
env.workspace = r"in_memory"
arcpy.env.scratchWorkspace = r"in_memory"


def main():
    # if os.path.exists(Export_folder):  ### JUST FOR TESTING¬¬¬
    #     shutil.rmtree(Export_folder)
    startTime = datetime.now()
    print('start time = {0}'.format(startTime))
    #
    try:
        # If directory has not yet been created
        os.makedirs(Export_folder)
    except OSError as e:
        # If directory has already been created and is accessible
        if os.path.exists(Export_folder):
            # arcpy.AddMessage("Error creating Export Directory. Directory Already Exists\n"
            #                  "############ Delete before running or rename. #############")
            sys.exit("Error creating Export Directory. Directory Already Exists\n"
                             "############ Delete before running or rename. #############")
        else:  # Directory cannot be created because of file permissions, etc.
            sys.exit("##### Cannot create Export Folder #####"
                     "### Check permissions and file path.###")


    scratch_gdb = os.path.join(Export_folder, "scratchFolder")
    if os._exists(scratch_gdb):
        shutil.rmtree(scratch_gdb)
    os.mkdir(scratch_gdb)

    shp_proc = check_bound_shp(bound_shp, area_field_name)
    raster_list = get_correct_time(Data_folder, start_date, end_date)

    shp_procFL = arcpy.MakeFeatureLayer_management(shp_proc, "lay_selec", "", r"in_memory")
    # fields = arcpy.ListFields(shp_procFL)
    # for field in fields:
    #     print(field.name)
    with arcpy.da.SearchCursor(shp_procFL, ['Zone_no', 'Area_Name']) as cursor:
        for row in cursor:
            expr = """{0} = {1}""".format('Zone_no', row[0])
            # print(expr)

            arcpy.SelectLayerByAttribute_management(shp_procFL,
                                                    "NEW_SELECTION",
                                                    expr)
            temp_zone = os.path.join(scratch_gdb, "temp_zone.shp")
            arcpy.CopyFeatures_management(shp_procFL, temp_zone)

            extent = arcpy.Describe(temp_zone).extent

            arcpy.env.extent = extent

            reqData = paralellProcess(temp_zone, raster_list)

            reqData = reqData.set_index('datetime').asfreq('5Min')

            reqData = reqData.resample(timestep).sum()

            # adding some more variables here
            xdim, ydim = get_raster_size(raster_list)

            reqData['Volume_m3'] = (reqData['tot_rainfall_mm']/1000) * xdim * ydim

            hourrate = pd.Timedelta('1Hour') / pd.Timedelta(timestep)
            reqData['VolRate_m3_hr'] = reqData['Volume_m3'] * hourrate

            reqData['mean_rain_rate_mm_hr'] = reqData['mean_rainfall_mm'] * hourrate

            reqData = reqData.fillna(0)

            col_order = ['mean_rainfall_mm',
                         'mean_rain_rate_mm_hr',
                         'Volume_m3',
                         'VolRate_m3_hr',
                         'tot_rainfall_mm',
                         'MAX',
                         'MIN',
                         'STD',
                         'Error_Rec']

            reqData = reqData[col_order]

            savePath = os.path.join(Export_folder, str(row[1]) + '_' + start_date + '_' + end_date + '.csv')
            if os.path.exists(savePath):
                os.remove(savePath)

            print('requested data provided now exporting as csv')
            reqData.to_csv(savePath, index=True)


    arcpy.Delete_management(scratch_gdb)
    finTime = datetime.now() - startTime
    print("script completed. \n"
          "Processing time = {0}".format(finTime))

def get_raster_size(raster_list):
    test_ras = raster_list[0]

    x_size = int(arcpy.GetRasterProperties_management(test_ras, "CELLSIZEX").getOutput(0))
    y_size = int(arcpy.GetRasterProperties_management(test_ras, "CELLSIZEY").getOutput(0))

    return x_size, y_size


def check_bound_shp(boundary_shp, f_name):
    sZone_fields = [f.name for f in arcpy.ListFields(boundary_shp)]

    if "Zone_no" in sZone_fields:
        arcpy.DeleteField_management(boundary_shp, "Zone_no")

    zone_info = os.path.join(scratch, "tmp_shp_copy")
    if arcpy.Exists(zone_info):
        arcpy.Delete_management(zone_info)
    arcpy.CopyFeatures_management(boundary_shp, zone_info)

    # create sequential numbers for reaches
    arcpy.AddField_management(zone_info, "Zone_no", "LONG")

    with arcpy.da.UpdateCursor(zone_info, ["Zone_no"]) as cursor:
        id=0
        for row in cursor:
            id += 1
            row[0] = id
            cursor.updateRow(row)

    result = arcpy.GetCount_management(zone_info)
    count = int(result.getOutput(0))
    print("number of features in boundary shaprefile is {0}".format(count))
    if count == 0:
        sys.exit("Error - boundary shp file provided contains no data!")
    elif count == 1:
        if f_name is None or f_name == "":
            if "Area_Name" in sZone_fields:
                arcpy.DeleteField_management(zone_info, "Area_Name")

            arcpy.AddField_management(zone_info, 'Area_Name', 'TEXT')
            with arcpy.da.UpdateCursor(zone_info, ['Area_Name']) as cursor:
                for row in cursor:
                    row[0] = "AOI"
                    cursor.updateRow(row)

        if f_name in sZone_fields:
            arcpy.AlterField_management(zone_info, f_name, new_field_name='Area_Name')

        print("single AOI provided - outputs")
    else:
        if f_name is None or f_name == "":
            sys.exit("######## Error - Aborting script ############ \n"
                     "Multiple shapes provided without unique names \n"
                     "### Add new field and create unique names ###")

        if f_name in sZone_fields:
            arcpy.AlterField_management(zone_info, f_name, new_field_name='Area_Name')

    return zone_info

def get_correct_time (ras_folder, start, end):
    print("retrieving raster names for requested time period: {0} - {1}".format(start, end))
    file_list = []

    for name in glob.glob(os.path.join(ras_folder, "*.tif")):
        file_list.append(name)# file_list.append(name)
    file_list.sort(key=lambda x: x[-30:-18])

    date_list = [s[-30:-18] for s in file_list] # gets list of dates form file list
    date_list = list(map(int, date_list))  # converts the list of dates to integers.

    if int(start) in date_list:
        s_row = [i for i, x in enumerate(file_list) if x[-30:-18] == start]
        s_row = int(s_row[0])
    else:
        closest_start = min(date_list, key=lambda x:abs(x-int(start)))
        s_row = [i for i, x in enumerate(file_list) if x[-30:-18] == str(closest_start)]
        s_row = int(s_row[0])

    if int(end) in date_list:
        e_row = [i for i, x in enumerate(file_list) if x[-30:-18] == end]
        e_row = int(e_row[0])
    else:
        closest_end = max(date_list, key=lambda x:abs(x-int(end)))
        e_row = [i for i, x in enumerate(file_list) if x[-30:-18] == str(closest_end)]
        e_row = int(e_row[0])


    selec_file_list = file_list[s_row:e_row]

    return selec_file_list


def iterateRasters(bound_area, ras_list):

    pandDFlist = []

    for ras in ras_list:

        date = ras[-30:-18]
        dateForm = date[:4] + '/' + date[4:6] + '/' + date[6:8] + ' ' + date[8:10] + ':' + date[10:12]
        datetime_object = datetime.strptime(dateForm, "%Y/%m/%d %H:%M")
        outTable = os.path.join(r'in_memory', "rain_radar_{0}").format(date)

        try:
            arcpy.sa.ZonalStatisticsAsTable(bound_area, "Zone_no", ras, outTable, "DATA", "ALL")

            arr = arcpy.da.TableToNumPyArray(outTable, ('SUM', 'MEAN', 'MAX', 'MIN', 'STD'))
            pandTab = pd.DataFrame(arr)
            pandTab['datetime'] = datetime_object
            pandTab = pandTab.rename(columns={"SUM": "tot_rainfall_mm"})
            pandTab['tot_rainfall_mm'] = pandTab['tot_rainfall_mm']/12
            pandTab = pandTab.rename(columns={"MEAN": "mean_rainfall_mm"})
            pandTab['mean_rainfall_mm'] = pandTab['mean_rainfall_mm'] / 12
            pandTab['Error_Rec'] = 0
            pandDFlist.append(pandTab)
        except Exception as e:
            print(e)
            print("Error occurred at: \n"
                  "{0}".format(ras))

            d = {'datetime': [datetime_object],
                 'tot_rainfall_mm': [0],
                 'mean_rainfall_mm': [0],
                 'MEAN': [0],
                 'MAX': [0],
                 'MIN': [0],
                 'STD': [0],
                 'Error_Rec': [999]}
            pandTab = pd.DataFrame(data=d)
            pandDFlist.append(pandTab)

    outPDdf = pd.concat(pandDFlist)

    return outPDdf

def paralellProcess(area_shp,Ras_list):
    n_feat = len(Ras_list)
    num_cores = multiprocessing.cpu_count() #- 1
    print('n available cores  = {0}'.format(num_cores))
    n_split = int(n_feat/num_cores)

    list_split = [Ras_list[i:i + n_split] for i in range(0, len(Ras_list), n_split)]

    pool = multiprocessing.Pool(num_cores)

    print("Creating data frame of requested time frame... \n"
          "Time to go parallel... This may take a while")

    function = partial(iterateRasters, area_shp)
    gdf = pd.concat(pool.map(function, list_split))

    pool.close()
    pool.join()

    return gdf

if __name__ == "__main__":
    main()
