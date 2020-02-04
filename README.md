# Rainfall_radar
To extract data from Metoffice rainfall radar. Includes facility to extract rainfall statistics for a polygon of choice (e.g. a river catchment boundary)

This README needs lots more work but essentially there are two folders here:  

1. The nimrod folder which provides tools to download and extract the data from the CEDA website.

2. The extraction script which is an R script which allows for the extraction of rainfall stats for a given AOI. This uses the exact extract package
which is a more precise way (and faster) of extracting raster stats.
