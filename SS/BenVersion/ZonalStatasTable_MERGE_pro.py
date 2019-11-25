import os, arcpy
from arcpy import env

# arcpy.env.extent = r"E:\Users\bwj202\OneDrive - University of Exeter\GIS\SWW_area_wo_Bournemouth.shp"

# Check out the ArcGIS Spatial Analyst extension license
env.cartographicCoordinateSystem = arcpy.SpatialReference("British National Grid")
env.outputCoordinateSystem = arcpy.SpatialReference("British National Grid")
env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")
Data_folder = os.path.join(os.getcwd(), "Exports")
env.workspace = r"in_memory"  # os.getcwd()
env.scratchWorkspace = r"in_memory"
Bound_folder = r"E:\Onedrive_exeter\OneDrive - University of Exeter\02 UST\02 Vector data\Catchment_boundary"

 #INSERT HERE
zoneField = "Name"

Export_folder = os.getcwd() + "/Tables"

if os.path.exists(Export_folder):
    pass
else:
    arcpy.CreateFolder_management(os.getcwd(), "Tables")

for filename in os.listdir(Bound_folder):
 if filename.split("_")[0] == "Bound":
  if filename.endswith(".shp"):
   print(filename)
   inZoneData = Bound_folder + "/" + filename
   for name in os.listdir(Data_folder):
     if name.endswith(".tif"):
       infile = Data_folder + "/" + name
       print(infile)
       outTable = Export_folder + "/" + "Table" + name.split("_")[2] + "_" + filename.split("_us")[0]
       print(outTable)
       outZSaT = ZonalStatisticsAsTable(inZoneData, zoneField, infile, outTable, "DATA", "ALL")