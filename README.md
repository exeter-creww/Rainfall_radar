# Rainfall_radar


To extract data from Metoffice rainfall radar. Includes facility to extract rainfall statistics for a polygon of choice (e.g. a river catchment boundary)
Instructions for use of Radar files from the Metoffice

Ben Jackson (b.w.jackson@exeter.ac.uk)


1)	Downloading the data
Rain radar data can be downloaded from the CEDA website, it is either available for Europe (http://catalogue.ceda.ac.uk/uuid/d5ae8b92d8c884690592ce619f2eca07), or for the UK alone (http://catalogue.ceda.ac.uk/uuid/f91b2c5399c5bf689e29bb15ab45da8a). 
The spatial resolution of both datasets is 5km, and the time resolution is every 15 minutes (please note: the description of the UK dataset states that data is available every 5 minutes, however for data I’ve looked at this is instead at the 15 minute resolution).
To download the data you must first put in a request, however, once you have filled out all the appropriate details, you will be given access immediately.
The download page breaks up files by year, so go to the first year of interest and work forward. To download more than one file at once you must use the top right hand search box:
 
To search for files, you should use the wildcard “ * ” to specify files that fall within the month of interest. For example, typing: “*201805*.dat.gz.tar” (without the “”), would return all .dat.gz.tar  files that contain data for May of 2018. The .dat format is the data format, which can be displayed within a GIS. 
I highly recommend you ONLY download files that you need! You will need considerable amount of disk space, so downloading extra will burden your PC with unnecessary data.

2)	Unzipping


Once the download is complete you will need to unzip the files from the .tar and .gz files. To do this manually would take you far too long. You can automate this using 7zip, which can be obtained from the Software Center (open start and type software center, it will come up in the search). OR downloaded from the 7zip website if you have administrative rights.
The advantage of 7zip is the capability of running it from the command prompt. 
 
Download unzip.bat stored in this repository and move it to the folder containing your downloaded files and double click it to run it. This will unzip all files.
You can now delete all “.tar” and “.gz” files, as they are no longer needed.
The files of interest are the “.dat” files.


3)	Preprocessing


Make sure you have a copy of ArcGIS desktop, and notepad++, which can be found in the software center.

We first need to convert the .dat files into a readable format.
To do so we will need the tool created by Alona Armstrong, which is made available on her website:
https://alonaarmstrong.wordpress.com/radar/
The file you need is found here (if this does not work, check Alona’s website in case it has changed): https://www.dropbox.com/sh/ws0r0z1zx34i7rf/AACERgM-UIwkzW3Xr6dGYNQpa?dl=0 
You need to download “a.exe” and “Nimrod2ascii.exe”. Save these files in the folder you unzipped the “.dat” files into.
Run “Nimrod2ascii.exe”, then drag all “.dat” files into the Nimrod2ascii window to convert the files, it may take some time…
 

The tool produces two sets of “.txt” files, one which contains your data in ascii format, and one that contains the header (those containing a “_header.txt” suffix), which contains metadata about your ascii data.
Create a subfolder called “data” within your folder containing the “.txt” files.

At the top of the window you can sort or filter each file by different parameters. Click on “Type” in the header (shown below), and select “Text Document” files. Now only “.txt” files will be displayed within the folder. Next, filter by “Size”, and tick the box next to “medium”. Now move all the “.txt” files that remain into the “data” folder.
 
 We can now convert the “.txt” files (that you just moved), to “.asc” format. Copy the file “rename.bat” from the repository, and paste it into your “Data” folder. Run the file and it will convert all .txt to .asc
 
Right click on one of your new “.asc” files, and click Edit with Notepad++, you should see a window similar to that shown below
 
If you see “******”, next to xllcorner and/or yllcorner, then you will need to edit these fields for every “.asc” file you have, so that the GIS can determine where this spatial data is located. To do this you will need to use the script below. 
 
Download "Coordedit2.py" from the depository; this fill may need to be edited. First copy it into the “Data” folder, then right click on it and select Edit with Notepad++. The script’s code will be displayed in Notepad++, as shown below
 
The numbers on the left are the line numbers. Line 14 and 15 contains the code you might need to edit. Look at line 14 and see where the code references “-405000\n", this is your x-coordinate (-405000), whereas line 15 contains the y-coordinate.
The correct co-ordinates can be found within the header files (the “.txt” files that you did not copy into the “Data” folder). Within the header files, the x coordinate is assigned to number 61 and the y-coordinate is assigned to number 64. Open a header file to see if the coordinates defined by 61 and 64 differ to that contained within the python script, if they do, then the script should be modified FOR THESE TWO LINES ONLY by replacing the existing numbers with that contained in the header, keep the “\n” and the inverted commas. So for example, if the x coordinate displayed in the header is actually 500000, then line 14 of the python code should be edited to read:-

replace_line(os.path.join(os.getcwd(), filename), 2, 13, 22," 500000\n")


If the coordinates match that which is in the code then you do not need to edit it. Next, save and close notepad++, then run "Coordedit2.py" by double clicking on it. Wait until the python window closes before proceeding.

The final step for preprocessing is to convert the .asc files to the TIF format and to convert the rainfall depth into mm. Copy “Conversion.py” from the repository (MAKE SURE YOU CHOOSE THE PYTHON FILE FOR YOUR VERSION OF ARCGIS), and move it into the folder the contains the data folder, but NOT into the data folder itself.
Edit the python file in Notepad++, and examine line 8:
arcpy.env.extent = r""

Within the inverted commas, insert the full path to a vector or raster file that covers the spatial extent of interest. For example, if you were interested only in Devon, you would choose a file that shows the boundary of Devon. It isn’t essential to set the spatial extent, but it will reduce the processing time considerably; if you decide to not include a spatial extent, then delete the entirety of line 8.
Make sure you do not remove the “r” before the inverted commas, that is necessary for the function to work!
 
Appendix 1 - Zonal statistics
-----------------------------

This section of this guide is for those that want to determine statistical information about rainfall within given catchment boundaries.
These catchment boundaries need to be in the polygon format, and the filenames must follow the structure of Boundaryname_us_bound.shp.

Download “Boundaries.py” (for your version of Arc) into the folder containing your catchment boundaries and run it; this will add the field “Name” to each boundary and then writes the catchment name to this field, derived from the filename.
If you have a lot of data you might prefer to combine your catchment boundaries, which should speed up the process considerably. However, you may only combine catchment boundaries that DO NOT overlap, so be careful if you decide to proceed with this step. If you do NOT want to combine the catchment boundaries then download the tool “ZonalStat_fordistribution.py” (again, for your version of arc). Place the python file into the folder that contains your “data” folder, discussed within section 3, but not within the data folder itself.


If you want to combine boundaries 
---------------------------------
  
To combine catchment boundaries, open ArcGIS and run the Merge tool. If a catchment boundary overlaps with another, then it can still be merged with boundaries that it does NOT overlap. Save your merged boundaries in the format of “Bound”[rest of filename here] (e.g. Bound_Exe, Boundexe etc.).  The tool in the depository: “ZonalStatasTable_MERGE.py” is to be used with your combined boundaries. If you are following this step then there is no need to use “ZonalStat_fordistribution.py”. Place the python file into the folder that contains your “data” folder, discussed within section 3, but not within the data folder itself.

**Follow the below steps regardless of whether you have combined boundaries or not**

"The python file" mentioned here refers to either the “ZonalStatasTable_MERGE.py” or the “ZonalStat_fordistribution.py” python file, depending on whether you combined boundaries or not.

Edit the python file in Notepad++ and note line 14:
 Bound_folder = r""
Within the inverted commas, insert the full path to the folder that contains all of your boundary data. Make sure you do not remove the “r” before the inverted commas, which is necessary for the function to work!

Don’t run the file yet. If you have ArcGIS Pro, then copy Radar.7z  into a folder of your choice:-
--------------

Unzip “Radar.7z” using 7zip, extracting to a folder of your choice. Edit “Radar_Merge.py” in Notepad++, and change lines: 16, 24, 30 and 47. You will need to replace “YOURPATHHERE” with the path to: 
Line 16 <-	The full path to the Datelist.xls file you extracted
Line 24	<- The full path to the Start_Table.dbf file you extracted
Line 30	<- The full path to the folder than contains your zonal statistics tables
Line 47	<- The full path to the folder that you want to save your final merged table to.

You also need to install the relevant libraries to python, so open the start menu, type “CMD” then press enter to open up the command prompt. Now type “pip install simpledbf” and press enter. Once this is complete type “pip install glob” and press enter. Once both are complete you may run the python file “Radar_Merge.py”.

If you use the Desktop version of ArcGIS, then first check to see which boundary has the longest name, then find a dbf within your tables folder than contains statistics regarding this boundary. Rename this file to “Final_table.dbf”. You may now run the python file.

Regardless of using Desktop or Pro version of ArcGIS, the python file which will produce a set of tables within the subfolder “Tables”, it will then merge these tables together to produce the table “Final_table.dbf”`.

