# Title     : Pre Processing of input geometries for extracting rainfall data
# Objective : to combine multiple input shp files into a single file and define a unique name value for each region
#             of interest.
# Created by: Hugh Graham
# Created on: 29/11/2019

#----------- Project Set Up --------------------------

#! /usr/bin/Rscript
.libPaths("C:/Program Files/R/R-3.6.1/library")
# Check that the required packages are installed
list.of.packages <- c("tidyverse", "sf", "rgdal", "ggmap")

new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages)

library(sf)
library(rgdal)
library(tidyverse)
library(ggmap)

# ------------------- User input -------------------------------------------

Polygon_folder <- "C:/HG_Projects/SideProjects/Radar_Test_Data"
Out_folder <- "C:/HG_Projects/SideProjects/Radar_Test_Data/Test_PP_outs"

# ------------------ Check Export folders ------------------------------------

if (isFALSE(dir.exists(Out_folder))){
  print("Export folder does not exist - creating it now...")
  dir.create(Out_folder)
} else {
  print("Export folder already exists")
}

check_img_file <- file.path(Out_folder, "check_images")

if (isFALSE(dir.exists(check_img_file))){
  dir.create(check_img_file)
}


# ---------------------- a few checks and finding all required files --------------------------------------
shp_list <- list.files(Polygon_folder, pattern = "\\.shp$") 

shp_path_list <-  paste(Polygon_folder, shp_list, sep="/")

outfile_name <- "merged_shapes"

EPSG <- 27700  # If working in UK and using MetOffice Rain Radar data leave this as 27700

epsg_df <- data.frame(make_EPSG())                                                     # get epsg dataframe from rgdal to compare proj4 and epsg codes

name <- basename(Polygon_folder)
str_replace(name, ".shp", "")

merged_shps = NULL

# --------------------- Check and set CRS for all shp files then merge into single df --------------

for (shp in shp_path_list) {
  
  name <- str_replace(basename(shp), ".shp", "")
  
  shape <- read_sf(dsn = shp)                                                      # Read in polygon(s)
  
  shape$Name <- name
  
  CRS <- as.numeric(na.omit(epsg_df$code[epsg_df$prj4 == crs(shape)]))                   # get the epsg code for the provided polgon
  
  if (CRS != EPSG){                                                                      # give message if original polygon not in OSGB.
    sprintf("%s not in correct CRS - transforming now...", basename(shp))
  }
  
  shape <- st_transform(shape, crs = EPSG)    
  
  merged_shps <- bind_rows(merged_shps, shape)
  
}

# Write Merged shp file - this is in the correct CRS - EPSG 27700
st_write(merged_shps, file.path(Out_folder, paste(outfile_name, "shp", sep = ".")))




# ---------------------- Create plot for each Polygon with background map ---------------------------------
# Note - these are reprojected in WGS84 to be compatible with the basemap

# for testing
# rg_gdf <-"C:/HG_Projects/SideProjects/Radar_Outputs/Res_Group_V2/run_shp/RG_Catchments_V2.shp" 
# rg_gdf <- read_sf(rg_gdf)
# merged_shps <- rg_gdf


for (i in 1:(nrow(merged_shps))){
  
  polyG <- st_transform(merged_shps[i,], crs = "+init=epsg:4326")
  polyG <- fortify(polyG)
  
  bb <- unname(c((st_bbox(polyG)[1] - 0.01),(st_bbox(polyG)[2] - 0.01), (st_bbox(polyG)[3] + 0.01), (st_bbox(polyG)[4] + 0.01)))
  
  nicemap <- get_map(bb, zoom = 13, source = "osm", maptype = "terrain")
  
  ggmap(nicemap)  +
    geom_sf(mapping = aes(geometry = geometry,
                          xmin = stat(x) - 0.1,
                          xmax = stat(x) + 0.1,
                          x = stat(x),
                          y = stat(y),) ,fill='grey',color='black', data=polyG, alpha=0, stat = "sf_coordinates") +
    theme_bw() +
    ggtitle(polyG$Name)
  
  ggsave(file.path(check_img_file, paste(polyG$Name, "jpeg", sep=".")))
  
}


