# Title     : ExactExtract function for Rainfall extraction
# Objective : calculate precise raster stats for catchment areas using the exact extract algorithm...
# Created by: hg340
# Created on: 22/11/2019


#! /usr/bin/Rscript
.libPaths("C:/Program Files/R/R-3.6.1/library")
# Check that the required packages are installed
list.of.packages <- c("exactextractr", "tidyverse", "raster", "sf")

new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages)

library(raster)
library(sf)
library(exactextractr)
library(tidyverse)



epsg = 27700

Data_folder <-  "D:/MetOfficeRadar_Data/UK_1km_Rain_Radar_Processed"
rasterlist <- list.files(Data_folder)
ras <- file.path(Data_folder , rasterlist[1000000])

shpfile <- "C:/HG_Projects/Event_Sep_R/Catchment_Area/Out_Catchments/Bud_Brook_Catch.shp"
# shpfile <- "C:/HG_Projects/SideProjects/Radar_Outputs/ResGroup_Catchments/shp_file/Res_Group_Catchments.shp"


shape <- read_sf(dsn = shpfile)
shape2 <- st_as_sf(shape)
plot(shape2[1])

grid <- raster(x = ras)

result <- exact_extract(grid, shape2, 'count')

result2 <- raster::extract(grid, shape2, fun=sum)

# exactextractr::


















