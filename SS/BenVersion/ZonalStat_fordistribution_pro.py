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
Boundary = r"C:\Users\bwj202\OneDrive - University of Exeter\GIS\Leakage\03 Bursts and Leakage\SWW DMA's Areas 1-6 12122018.shp"

zoneField = "DMA"

Export_folder = os.getcwd() + "/Tables"

if os.path.exists(Export_folder):
    pass
else:
    arcpy.CreateFolder_management(os.getcwd(), "Tables")


for name in os.listdir(Data_folder):
     if name.endswith(".tif"):
       infile = Data_folder + "/" + name
       print(infile)
       outTable = Export_folder + "/" + "Table" + name.split("_")[2]
       print(outTable)
       outZSaT = arcpy.sa.ZonalStatisticsAsTable(Boundary, zoneField, infile, outTable, "DATA", "ALL")
