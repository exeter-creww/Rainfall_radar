import os, arcpy
from collections import defaultdict
from arcpy import env
from arcpy.sa import *
from datetime import datetime
startTime = datetime.now()

arcpy.env.extent = r"" #Insert extent file here

# Check out the ArcGIS Spatial Analyst extension license
arcpy.env.cartographicCoordinateSystem = arcpy.SpatialReference("British National Grid")
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("British National Grid")
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")
Data_folder = os.path.join(os.getcwd(), "data")
env.workspace = r"in_memory"  # os.getcwd()
arcpy.env.scratchWorkspace = r"in_memory"

print (Data_folder)

Export_folder = os.getcwd() + "/Exports"

if os.path.exists(Export_folder):
    pass
else:
    arcpy.CreateFolder_management(os.getcwd(), "Exports")

dictdata = defaultdict(list)
for filename in os.listdir(Data_folder):
  if filename.endswith('.asc'):
        # convert nodata to zero
        print(filename)
        raster = os.path.join(Data_folder, filename)
        print(raster)
        out1 = Con(IsNull(arcpy.Raster(raster)), 0, arcpy.Raster(raster))
  out2 = out1 / 32
  # save final output
  out2.save(Export_folder + "/" + filename + ".tif")

print ("finished")

