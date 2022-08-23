# taken from the CEDA website - some modifications made for the Radar data

# Import required python modules
import ftplib
import os
from tqdm import tqdm

# Define the local directory name to put data in
ddir=os.path.abspath("D:/MetOfficeRadar_Data/UK_1km_Rain_Radar_raw_update")

def main():
    # If directory doesn't exist make it
    if not os.path.isdir(ddir):
        os.mkdir(ddir)

    # Change the local directory to where you want to put the data
    os.chdir(ddir)

    # login to FTP
    f = ftplib.FTP("ftp.ceda.ac.uk", "****UserName****", "****Password*****")

    Year1 = input('Year start: ')
    Year2 = input('Year end: ')

    # loop through years
    for year in tqdm(range(int(Year1), int(Year2))):

        # loop through months
        for month in range(1, 13):

            # get number of days in the month
            if year%4==0 and month==2:
                ndays=29
            else:
                ndays=int("dummy 31 28 31 30 31 30 31 31 30 31 30 31".split()[month])

            # loop through days
            for day in range(1, ndays+1):

                # # loop through hours
                # for hour in range(0, 19, 6):
                #
                #     # loop through variables
                #     for var in ("10u", "10v"):

                # change the remote directory
                try:
                    f.cwd("/badc/ukmo-nimrod/data/composite/uk-1km/%.4d" % year) # ukmo-nimrod/data/composite/uk-1km/%.4d/%.2d/%.2d
                    # define filename
                    file = "metoffice-c-band-rain-radar_uk_%.4d%.2d%.2d_1km-composite.dat.gz.tar" % (year, month, day)
                    # get the remote file to the local directory
                    f.retrbinary("RETR %s" % file, open(file, "wb").write)
                except ftplib.error_perm as e:
                    print(e)
                    pass

    # Close FTP connection
    f.close()

if __name__ == "__main__":
    main()

