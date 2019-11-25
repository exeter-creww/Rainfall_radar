import os, arcpy
from arcpy import env

arcpy.env.extent = r"E:\Users\bwj202\OneDrive - University of Exeter\GIS\SWW_area_wo_Bournemouth.shp" #Insert boundary data here

# Check out the ArcGIS Spatial Analyst extension license
arcpy.env.cartographicCoordinateSystem = arcpy.SpatialReference("British National Grid")
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("British National Grid")
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")
Data_folder = os.path.join(os.getcwd(), "Exports")
env.workspace = r"in_memory"  # os.getcwd()
arcpy.env.scratchWorkspace = r"in_memory"
Bound_folder = r""

zoneField = "Name"

Export_folder = os.getcwd() + "/Tables"

if os.path.exists(Export_folder):
    pass
else:
    arcpy.CreateFolder_management(os.getcwd(), "Tables")

for filename in os.listdir(Bound_folder):
 if filename.endswith("bound.shp"):
  inZoneData = Bound_folder + "/" + filename
  for name in os.listdir(Data_folder):
     if name.endswith(".tif"):
       infile = Data_folder + "/" + name
       print(infile)
       outTable = Export_folder + "/" + "Table" + name.split("_")[2] + "_" + filename.split("_us")[0]
       print(outTable)
       outZSaT = arcpy.sa.ZonalStatisticsAsTable(inZoneData, zoneField, infile, outTable, "DATA", "ALL")

env.workspace = Export_folder
      
for table in arcpy.ListTables("*"):  
    name = table.split("table")[1]
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