import os, arcpy
from arcpy.sa import *
from arcpy import env
import sys
import glob
from datetime import datetime
import pandas as pd
# arcpy.env.extent = r"E:\Users\bwj202\OneDrive - University of Exeter\GIS\SWW_area_wo_Bournemouth.shp"

# Check out the ArcGIS Spatial Analyst extension license
arcpy.env.cartographicCoordinateSystem = arcpy.SpatialReference("British National Grid")
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("British National Grid")
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")


Data_folder = os.path.abspath("Y:/shared_data/01_Radar/01_Converted_15_minutes_data/Exports_2004_2011")

bound_shp = os.path.abspath("C:/HG_Projects/SideProjects/Rainfall_radar/Test_data/Otter_catchment/river_otter_catch.shp")

Export_folder = os.path.abspath("C:/HG_Projects/SideProjects/Rainfall_radar/Test_Exports")

area_field_name = "FieldName"

start_date = '200703010600'
end_date = '200704010600'

scratch = r"in_memory" # consider making this a geodatabase - possible RAM limitations may occur...
env.workspace = r"in_memory"  # os.getcwd()
arcpy.env.scratchWorkspace = r"in_memory"


def main():
    try:
        # If directory has not yet been created
        os.makedirs(Export_folder)
    except OSError as e:
        # If directory has already been created and is accessible
        if os.path.exists(Export_folder):
            arcpy.AddMessage("Error creating Export Directory. Directory Already Exists\n"
                             "############ Delete before running or rename. #############")
            sys.exit("Error creating Export Directory. Directory Already Exists\n"
                             "############ Delete before running or rename. #############")
        else:  # Directory cannot be created because of file permissions, etc.
            sys.exit("##### Cannot create Export Folder #####"
                     "### Check permissions and file path.###")
    shp_proc = check_bound_shp(bound_shp, area_field_name)
    raster_list = get_correct_time (Data_folder, start_date, end_date)

    shp_procFL = arcpy.MakeFeatureLayer_management(shp_proc, "lay_selec", "", r"in_memory")

    with arcpy.da.SearchCursor(shp_procFL, ['Zone_no', 'Area_Name']) as cursor:
        for row in cursor:
            expr = """{0} = '{1}'""".format('Zone_no', row[0])
            # print(expr)

            arcpy.SelectLayerByAttribute_management(shp_procFL,
                                                    "NEW_SELECTION",
                                                    expr)
            temp_zone = r"in_memory/OS_tempZone"
            arcpy.CopyFeatures_management(shp_procFL, temp_zone)

            extent = arcpy.Describe(temp_zone).extent
            xmin = extent.XMin
            ymin = extent.YMin
            xmax = extent.XMax
            ymax = extent.YMax

            arcpy.env.extent = (xmin, ymin, xmax, ymax)

            iterateRasters(temp_zone, raster_list, Export_folder)



def check_bound_shp(boundary_shp, f_name):
    sZone_fields = [f.name for f in arcpy.ListFields(boundary_shp)]

    if "Zone_no" in sZone_fields:
        arcpy.DeleteField_management(boundary_shp, "Zone_no")

    zone_info = os.path.join(scratch, "tmp_shp_copy")
    if arcpy.Exists(zone_info):
        arcpy.Delete_management(zone_info)
    arcpy.CopyFeatures_management(boundary_shp, zone_info)

    # create sequential numbers for reaches
    fieldName = "Zone_no"
    expression = "autoIncrement()"
    codeblock = """
    rec = 0
    def autoIncrement():
            global rec
            pStart = 1
            pInterval = 1
            if (rec == 0): 
                rec = pStart 
            else:
                rec = rec + pInterval 
            return rec"""
    # Execute AddField
    arcpy.AddField_management(zone_info, fieldName, "LONG")
    # Execute CalculateField
    arcpy.CalculateField_management(zone_info, fieldName, expression, "PYTHON_9.3", codeblock)

    result = arcpy.GetCount_management(zone_info)
    count = int(result.getOutput(0))
    if count == 0:
        sys.exit("Error - boundary shp file provided contains no data!")
    elif count == 1:
        if f_name is None or f_name == "":
            if "Area_Name" in sZone_fields:
                arcpy.DeleteField_management(zone_info, "Area_Name")

            arcpy.AddField_management(zone_info, 'Area_Name', "TEXT")
            with arcpy.da.UpdateCursor(zone_info, f_name) as cursor:
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
    file_list.sort(key=lambda x: x[106:118])

    date_list = [s[106:118] for s in file_list] # gets list of dates form file list
    date_list = list(map(int, date_list))  # converts the list of dates to integers.

    if int(start) in date_list:
        s_row = [i for i, x in enumerate(file_list) if x[106:118] == start]
        s_row = int(s_row[0])
    else:
        closest_start = min(date_list, key=lambda x:abs(x-int(start)))
        s_row = [i for i, x in enumerate(file_list) if x[106:118] == str(closest_start)]
        s_row = int(s_row[0])

    if int(end) in date_list:
        e_row = [i for i, x in enumerate(file_list) if x[106:118] == end]
        e_row = int(e_row[0])
    else:
        closest_end = max(date_list, key=lambda x:abs(x-int(end)))
        e_row = [i for i, x in enumerate(file_list) if x[106:118] == str(closest_end)]
        e_row = int(e_row[0])


    selec_file_list = file_list[s_row:e_row]

    return selec_file_list


def iterateRasters(bound_area, ras_list, Export_folder):

    for ras in ras_list:
        date = ras[106:118]
        datetime_object = datetime.strptime(date, "%Y%m%d%H%M%S")
        outTable = os.path.join(r"in_memory", "rain_radar_{0}").format(date)
        arcpy.sa.ZonalStatisticsAsTable(bound_area, "Zone_no", ras, outTable, "DATA", "ALL")

        arr = arcpy.da.TableToNumPyArray(outTable, ('SUM', 'MEAN', 'MEDIAN', 'MAX', 'MIN', 'STD'))
        arr['datetime'] = datetime_object



    # for filename in os.listdir(bound_area):
    #  if filename.split("_")[0] == "Bound":
    #   if filename.endswith(".shp"):
    #    print(filename)
    #    inZoneData = bound_area + "/" + filename
    #    for name in os.listdir(Data_folder):
    #      if name.endswith(".tif"):
    #        infile = Data_folder + "/" + name
    #        print(infile)
    #        outTable = Export_folder + "/" + "Table" + name.split("_")[2] + "_" + filename.split("_us")[0]
    #        print(outTable)
    #        outZSaT = arcpy.sa.ZonalStatisticsAsTable(inZoneData, "Zone_no", infile, outTable, "DATA", "ALL")

    env.workspace = Export_folder

    for table in arcpy.ListTables("*"):
        name = table.split("Table")[1]
        print ("Name is: ", name)
        date = name[0:8]
        print ("Date is: ", date)
        time = name[8:12]
        print ("Time is: ", time)
        arcpy.AddField_management(table, "Date", "TEXT")
        arcpy.AddField_management(table, "Time", "TEXT")
        arcpy.CalculateField_management(table, "Date", '"' + date + '"', "PYTHON")
        arcpy.CalculateField_management(table, "Time", '"' + time + '"', "PYTHON")

    output = Export_folder + "/Final_table.dbf"
    arcpy.Merge_management(arcpy.ListTables("*"), output)


if __name__ == "__main__":
    main()
