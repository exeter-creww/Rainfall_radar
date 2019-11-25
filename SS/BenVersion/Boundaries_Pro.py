import os, arcpy
from arcpy import env


# Check out the ArcGIS Spatial Analyst extension license
env.cartographicCoordinateSystem = arcpy.SpatialReference("British National Grid")
env.outputCoordinateSystem = arcpy.SpatialReference("British National Grid")
env.overwriteOutput = True
Data_folder = os.getcwd()
env.workspace = os.getcwd()
env.scratchWorkspace = os.getcwd()

for filename in os.listdir(Data_folder):
 if filename.endswith("bound.shp"):
   infile = Data_folder + "/" + filename
   print(infile)
   Catch = filename.split("_us")[0]
   arcpy.AddField_management(infile, "Name", "TEXT")
   arcpy.CalculateField_management(infile, "Name", '"' + Catch + '"', "PYTHON")