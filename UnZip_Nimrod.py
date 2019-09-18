# This script extracts all of the downloaded data to a new folder.


import os
import glob
import shutil
import gzip


# ddir=os.path.abspath("D:/MetOfficeRadar_Data/UK_1km_Rain_Radar/")
ddir=os.path.abspath("D:/MetOfficeRadar_Data/Data/")
edir = os.path.join(ddir, 'Extracted')

def main():
    if not os.path.isdir(edir):
        os.mkdir(edir)

    for name in glob.glob(os.path.join(ddir, "*_1km-composite.dat.gz.tar")):
        print('extracting file: {0}'.format(name))

        shutil.unpack_archive(filename=name, extract_dir=edir)


    for name in glob.glob(os.path.join(edir, "*_1km-composite.dat.gz")):
        print('decompressing file: {0}'.format(name))

        inFile = gzip.GzipFile(name, 'rb')
        s = inFile.read()
        inFile.close()
        output = open(name[:-3], 'wb')
        output.write(s)
        output.close()

        print("now delete intermediate file...")
        os.remove(name)

if __name__ == "__main__":
    main()
