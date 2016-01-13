#!/usr/bin/python

import cgi
from os import path, system, mkdir
from template import bulkdownload


form = cgi.FieldStorage()
zipFile = form["zipFile"]
zipFilename = zipFile.filename
zipData = zipFile.file.read()


uploadedZipFilename = path.join("/downloads/bulk", zipFilename)
uploadedZipFile = open(uploadedZipFilename,"wb")
uploadedZipFile.write(zipData)
uploadedZipFile.close()

unzippedFoldername = path.join("/downloads/enabulk")
try: discard =  mkdir(unzippedFoldername)
except OSError: pass
discard = system("unzip -o -d %s %s" % (unzippedFoldername, uploadedZipFilename))


allEnaFiles = path.join(unzippedFoldername, zipFilename.replace(".zip",""), "*")

bulkEnaFile = path.join(unzippedFoldername, "%s_bulk.txt" % zipFilename.replace(".zip",""))

dicard = system("cat %s >> %s" % (allEnaFiles, bulkEnaFile))


bulkEnaFile = path.join(unzippedFoldername, "%s_bulk.txt" % zipFilename.replace(".zip",""))
bulk_html = bulkdownload % (bulkEnaFile, "%s_bulk.txt" % zipFilename.replace(".zip",""))

print "Content-type: text/html\n\n";
print bulk_html
print allEnaFiles
print bulkEnaFile