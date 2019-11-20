# Script builds rainfall time series from Nimrod MetOffice rainfall data. Data must already be converted into an
# ESRI readable Raster Format.

#Version uses open source products namely: geopandas, rasterio and rasterstats


import os
import multiprocessing
import sys
import glob
import pandas as pd
# from tqdm import tqdm # JUST FOR TESTING...
from functools import partial
from datetime import datetime
import shutil
import rasterio
from rasterstats import zonal_stats
import geopandas as gpd


# Data_folder = os.path.abspath("Y:/shared_data/01_Radar/01_Converted_15_minutes_data/Exports_2012_2018")
Data_folder = os.path.abspath("D:/MetOfficeRadar_Data/UK_1km_Rain_Radar_Processed")

bound_shp = os.path.abspath("C:/HG_Projects/Event_Sep_R/Catchment_Area/Out_Catchments/Bud_Brook_Catch.shp")
# bound_shp = os.path.abspath("C:/HG_Projects/SideProjects/Radar_Outputs/ResGroup_Catchments/shp_file/Res_Group_Catchments.shp")


# Export_folder = os.path.abspath("C:/HG_Projects/SideProjects/Radar_Outputs/ResGroup_Catchments/Exports_RG")
# Export_folder = os.path.abspath("C:/HG_Projects/SideProjects/Radar_Test_Data/Test_Exports")
Export_folder = os.path.abspath("C:/HG_Projects/Event_Sep_R/Radar_Rain_Exports_Correct")

area_field_name = None #"Name"  # this is the name of the attribute you want to use to name your files.

# start_date = '201908050000' # Let's test things...
# end_date = '201908162355'

start_date = '200907090000'
end_date = '201904040900'
#
# start_date = '201001010000'
# end_date = '201909162355'  # This is the most recent observation we currently have downloaded.

timestep = '15Min'   # set the desired time step for rainfall time series minimum of '5Min'. other options: 'D' for daily,
                     # 'W' for weekly. for more info look up pandas resample.

epsg_code = str(27700)

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

            print("Error creating Export Directory. Directory Already Exists\n"
                             "############ Delete before running or rename. #############")

        else:  # Directory cannot be created because of file permissions, etc.
            sys.exit("##### Cannot create Export Folder #####"
                     "### Check permissions and file path.###")


    scratch_gdb = os.path.join(Export_folder, "scratchFolder")
    if os._exists(scratch_gdb):
        shutil.rmtree(scratch_gdb)
    os.mkdir(scratch_gdb)

    shp_proc_gdf = check_bound_shp(bound_shp, area_field_name, epsg_code)
    raster_list = get_correct_time(Data_folder, start_date, end_date)

    for i, area in shp_proc_gdf.iterrows():

        gdf = pd.DataFrame(area).transpose()

        name = gdf.iloc[0]['Area_Name']

        reqData = paralellProcess(gdf, raster_list)

        reqData = reqData.set_index('datetime').asfreq('5Min')

        reqData1 = reqData[['mean_rainfall_mm', 'tot_rainfall_mm']].resample(timestep).sum()
        reqData2 = reqData[['max',  'std', 'Error_Rec']].resample(timestep).max()
        reqData3 = reqData['min'].resample(timestep).min()
        dfs = [reqData1, reqData2, reqData3]
        reqData = dfs[0].join(dfs[1:])
        # adding some more variables here
        xdim, ydim = get_raster_size(raster_list)
        print('Raster dimensions are: x = {0} and y = {1}'.format(xdim, ydim))

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
                     'max',
                     'min',
                     'std',
                     'Error_Rec']

        reqData = reqData[col_order]

        reqData = reqData.drop(['tot_rainfall_mm'], axis=1)

        reqData = reqData.rename(columns={"max": "max_rain_rate_mm_hr"})
        reqData = reqData.rename(columns={"min": "min_rain_rate_mm_hr"})
        reqData = reqData.rename(columns={"std": "std_rain_rate_mm_hr"})

        savePath = os.path.join(Export_folder, str(name) + '_' + start_date + '_' + end_date + '.csv')
        if os.path.exists(savePath):
            os.remove(savePath)

        print('requested data provided now exporting as csv')
        reqData.to_csv(savePath, index=True)

    shutil.rmtree(scratch_gdb)
    # arcpy.Delete_management(scratch_gdb)
    finTime = datetime.now() - startTime
    print("script completed. \n"
          "Processing time = {0}".format(finTime))

def get_raster_size(raster_list):
    test_ras = raster_list[0]

    raster = rasterio.open(test_ras)
    gt = raster.transform

    x_size = gt[0]
    y_size = -gt[4]

    raster.close()

    return x_size, y_size


def check_bound_shp(boundary_shp, f_name, epsg):

    bound_gdf = gpd.read_file(boundary_shp, driver="ESRI Shapefile")
    bound_gdf.crs = {'init': epsg}

    bound_gdf['Zone_no'] = bound_gdf.index + 1

    count = len(bound_gdf.index)

    print("number of features in boundary shaprefile is {0}".format(count))
    if count == 0:
        sys.exit("Error - boundary shp file provided contains no data!")
    elif count == 1:
        if f_name is None or f_name == "":

            bound_gdf['Area_Name'] = 'AOI'

        if f_name in bound_gdf.columns:
            bound_gdf = bound_gdf.rename(columns={f_name: 'Area_Name'})

        print("single AOI provided - outputs")
    else:
        if f_name is None or f_name == "":
            sys.exit("######## Error - Aborting script ############ \n"
                     "Multiple shapes provided without unique names \n"
                     "### Add new field and create unique names ###")

        if f_name in bound_gdf.columns:
            bound_gdf = bound_gdf.rename(columns={f_name: 'Area_Name'})

    return bound_gdf

def get_correct_time (ras_folder, start, end):
    print("retrieving raster names for requested time period: {0} - {1}".format(start, end))
    file_list = []

    for name in glob.glob(os.path.join(ras_folder, "*.tif")):
        file_list.append(name)
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
    gs = gpd.GeoSeries(bound_area['geometry'])
    pandDFlist = []

    for ras in ras_list:

        date = ras[-30:-18]
        dateForm = date[:4] + '/' + date[4:6] + '/' + date[6:8] + ' ' + date[8:10] + ':' + date[10:12]
        datetime_object = datetime.strptime(dateForm, "%Y/%m/%d %H:%M")
        outTable = os.path.join(r'in_memory', "rain_radar_{0}").format(date)

        try:
            stats = zonal_stats(gs, ras, all_touched=True,
                                stats=['sum', 'mean', 'max', 'min', 'std'])
            err = 0
        except Exception as e:
            print(e)
            print(ras)

            stats = {'sum': [0],
                 'mean': [0],
                 'max': [0],
                 'min': [0],
                 'std': [0]}

            err = 999

        pandTab = pd.DataFrame(stats)

        pandTab['datetime'] = datetime_object
        pandTab = pandTab.rename(columns={"sum": "tot_rainfall_mm"})
        pandTab['tot_rainfall_mm'] = (pandTab['tot_rainfall_mm'] / 32) / 12  # must divide by 32 first as raster cells are (mm/hr)*32
        pandTab = pandTab.rename(columns={"mean": "mean_rainfall_mm"})
        pandTab['mean_rainfall_mm'] = (pandTab['mean_rainfall_mm'] / 32) / 12
        pandTab['max'] = (pandTab['max'] / 32) / 12
        pandTab['min'] = (pandTab['min'] / 32) / 12
        pandTab['std'] = (pandTab['std'] / 32) / 12

        pandTab['Error_Rec'] = err
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
