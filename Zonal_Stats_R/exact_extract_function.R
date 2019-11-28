# Title     : ExactExtract function for Rainfall extraction
# Objective : calculate precise raster stats for catchment areas using the exact extract algorithm...
# Created by: hg340
# Created on: 22/11/2019

# ----------- timer ------------

s_time <- Sys.time()

sprintf("start time = %s", s_time)

#----------- Project Set Up --------------------------

#! /usr/bin/Rscript
.libPaths("C:/Program Files/R/R-3.6.1/library")
# Check that the required packages are installed
list.of.packages <- c("exactextractr", "tidyverse", "raster", "sf", "rgdal", "lubridate", "foreach", "doParallel")

new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages)

library(raster)
library(sf)
library(rgdal)
library(exactextractr)
library(tidyverse)
library(lubridate)
library(foreach)
library(doParallel)

options(scipen=999)
#---------- Project Paths - User input ----------------------

Data_folder <- "D:/MetOfficeRadar_Data/UK_1km_Rain_Radar_Processed"  # Folder containing all Rainfall Rasters

bound_shp <- "C:/HG_Projects/Event_Sep_R/Catchment_Area/Out_Catchments/Bud_Brook_Catch.shp"  # An input polygon file
# bound_shp <- "C:/HG_Projects/SideProjects/Radar_Outputs/ResGroup_Catchments/shp_file/Res_Group_Catchments.shp"



Export_folder <- "C:/HG_Projects/SideProjects/Radar_Test_Data/Test_Exports3"  # An output folder for saving 
# Export_folder = os.path.abspath("C:/HG_Projects/Event_Sep_R/Radar_Rain_Exports_Correct")
# Export_folder = os.path.abspath("C:/HG_Projects/SideProjects/Radar_Outputs/ResGroup_Catchments/Exports_RG")


area_field_name = NA #"Name" # This is the name of the attribute you want to use to name your files. 
                             # if you only have one shape you can set as NA and a default of AOI is used

start_date <- 201908050000 # Let's test things... 200404062320 #
end_date <- 201909050000

timestep <- '15 min' # The desired timestep to aggregate files requires lubridate time format.

EPSG <- 27700  # If working in UK and using MetOffice Rain Radar data leave this as 27700

#--------------------- Check export folder ----------------------------------------------------

if (isFALSE(dir.exists(Export_folder))){
  print("Export folder does not exist - creating it now...")
  dir.create(Export_folder)
} else {
  print("Export folder already exists")
}

folder_5min <- file.path(Export_folder, "5_min_data")

if (isFALSE(dir.exists(folder_5min))){
  dir.create(folder_5min)
}

folder_Xmin <- file.path(Export_folder, sprintf("%s_data", str_replace(timestep, " ", "_")))

if (isFALSE(dir.exists(folder_Xmin))){
  dir.create(folder_Xmin)
}

# --------------- check polygon features --------------------------------------------------

shape <- read_sf(dsn = bound_shp)                                                      # Read in polygon(s)

epsg_df <- data.frame(make_EPSG())                                                     # get epsg dataframe from rgdal to compare proj4 and epsg codes

CRS <- as.numeric(na.omit(epsg_df$code[epsg_df$prj4 == crs(shape)]))                   # get the epsg code for the provided polgon

if (CRS != EPSG){                                                                      # give message if original polygon not in OSGB.
  print("Supplied polygons not in correct CRS - transforming now...")
}

shape <- st_transform(shape, crs = CRS)                                                # transform anyway to clarify epsg code if NA

count = nrow(shape)

if (count == 0) {
 stop("Error - boundary shp file provided contains no features!")
} else if (count == 1) {
  if (is.na(area_field_name)){
    shape$Area_Name <- "AOI"   # add AOI name
  }   
  if (area_field_name %in% colnames(shape)){
    shape <- shape %>% 
      rename(area_field_name = Area_Name)
  }
  
} else if (count > 1) {
  if (is.na(area_field_name)){
    stop(" ####### Aborting script ############ \n 
        ######## Multiple shapes provided without unique names \n 
        ######## Add new field and create unique names")
  }
  if (area_field_name %in% colnames(shape)){
    shape <- shape %>% 
      rename(Area_Name = area_field_name)
  }
  
}


shape <- shape %>%
  add_column(shp_area = st_area(shape))

#--------------------- Select desired rasters for processing ----------------------------------

rasterlist <- list.files(Data_folder, pattern = "\\.tif$")                              # retrieve all raster files from folder
rasterlist <- rasterlist[order(as.numeric(substr(rasterlist, start = 32, stop = 43)))]  # make sure they are in order

date_list <-  as.numeric(substr(rasterlist, start = 32, stop = 43))                     # Create numeric list of date times

if (start_date %in% date_list){                                                         # retrieve start date/time index
  s_row <- base::match(start_date, date_list)
  print(sprintf("Start date/time is: %1.0f", date_list[s_row]))
} else {                                                                                  # if requested start date/time not available get nearest
  
  s_row <- which(abs(date_list-start_date)==min(abs(date_list-start_date)))
  print(sprintf("Start date/time not available - choosing nearest date: %1.0f", date_list[s_row]))
}

if (end_date %in% date_list){                                                           # retrieve end date/time index
  e_row <- base::match(end_date, date_list)
  print(sprintf("End date/time is: %1.0f", date_list[e_row]))
} else {                                                                                  # if requested end date/time not available get nearest
  
  e_row <- which(abs(date_list-end_date)==min(abs(date_list-end_date)))
  print(sprintf("End date/time not available - choosing nearest date: %1.0f", date_list[e_row]))
}


selec_file_list = rasterlist[s_row:e_row]                                               # subset the list of rasters to get list of desired rasters


#-------------- Run Raster Statistics with exactextractr ----------------------------

substrRight <- function(x, n){       # function to extact substrings from right
  substr(x, nchar(x)-n+1, nchar(x))
}


selec_rasters <-  paste(Data_folder, selec_file_list, sep="/")

# combined_df <- NULL

#setup parallel backend to use many processors
cores=detectCores()
cl <- makeCluster(cores[1]-1) #not to overload your computer
registerDoParallel(cl)

# run rainfall extraction
combined_df <- foreach(ras = selec_rasters, .combine = rbind, 
                       .packages = c("raster", "sf", "rgdal", "exactextractr", "tidyverse", "lubridate" )) %dopar% {
  
  date_num <- substr(substrRight(ras, 30), start = 1, stop = 12)
  date_form <- paste(substr(date_num, 1,4), substr(date_num, 5,6), substr(date_num, 7,8), sep = "/")
  time_form <- paste(substr(date_num, 9,10), substr(date_num, 11,12), sep = ":")
  date_time_ex <-  ymd_hm(paste(date_form, time_form, sep = " "))
  
  grid <- raster(x = ras)
  
  result <- as.tibble(exact_extract(grid, shape, fun = c('mean','sum', 'min', 'max'), progress = FALSE))%>%
    rename(rain_intensity_mmhr = mean)%>%
    mutate(rain_intensity_mmhr = rain_intensity_mmhr/32) %>%
    rename(rain_volume_m3 = sum) %>%
    add_column(shp_area = as.double(shape$shp_area)) %>%
    mutate(rain_volume_m3 = (rain_volume_m3/32/12/1000)*shp_area) %>%
    rename(min_intensity_mmhr = min) %>%
    mutate(min_intensity_mmhr = min_intensity_mmhr/32) %>%
    rename(max_intensity_mmhr = max) %>%
    mutate(max_intensity_mmhr = max_intensity_mmhr/32) %>%
    add_column(Area_Name = shape$Area_Name) %>%
    add_column(date_time = date_time_ex)
  
  # combined_df <- rbind(combined_df,result)
}

combined_df <- combined_df %>%
  group_by(Area_Name)

table_list <- group_split(combined_df)


for (tab in table_list){
  name <- tab$Area_Name[1]
  
  tab <- tab %>%
    select(date_time, rain_intensity_mmhr, rain_volume_m3, min_intensity_mmhr, max_intensity_mmhr)
  

  write_csv(tab , path = file.path(folder_5min, 
                                     paste(name, "5_min", as.character(start_date), 
                                           as.character(paste(end_date, "csv", sep = ".")), sep = "_")))
  
  resam_tab <- tab %>% 
    group_by(requested_interval = ceiling_date(date_time, unit = timestep)) %>% 
    summarise(rain_intensity_mmhr = mean(rain_intensity_mmhr),
              rain_volume_m3 = sum(rain_volume_m3),
              min_intensity_mmhr = min(min_intensity_mmhr),
              max_intensity_mmhr = max(max_intensity_mmhr))%>%
    # mutate(requested_interval = requested_interval + minutes(15))%>%
    rename(date_time = requested_interval)
  
  write_csv(resam_tab , path = file.path(folder_Xmin, 
                                   paste(name, str_replace(timestep, " ", "_"), as.character(start_date), 
                                         as.character(paste(end_date, "csv", sep = ".")), sep = "_")))
}


sprintf("script completed check %s for results", Export_folder)
print(Sys.time() - s_time)



