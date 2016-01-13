#!/usr/bin/env python

import time
import cgi
from os import path, system, mkdir

from template import imgtdownload
from make_imgt_files import write_imgt_files
import datetime

imgtInput_BaseLoc = "/downloads/imgtinput"
foldername = datetime.datetime.now().strftime('imgt_%d_%m_%Y_%H-%M')
imgtInputPath = path.join(imgtInput_BaseLoc, foldername)
discard = mkdir(imgtInputPath)

form = cgi.FieldStorage()

enaZipFile = form["enaZipFile"]
enaZipFilename = enaZipFile.filename
enaZipData = enaZipFile.file.read()

enaZipWritePath = path.join(imgtInputPath, enaZipFilename)
enaZipWriter = open(enaZipWritePath, "wb")
enaZipWriter.write(enaZipData)
enaZipWriter.close()

discard = system("unzip -o -d %s %s" % (imgtInputPath, enaZipWritePath))
enaFilesPath = enaZipWritePath.split(".")[0]

enaEmailFile = form["enaEmailFile"]
enaEmailFilename = enaEmailFile.filename
enaEmail = enaEmailFile.file.read()

enaEmailWritePath = path.join(imgtInputPath, enaEmailFilename)
enaEmailWriter = open(enaEmailWritePath, "w")
enaEmailWriter.write(enaEmail)
enaEmailWriter.close()

befundFile = form["befundFile"]
befundFilename = befundFile.filename
befund = befundFile.file.read()

befundWritePath = path.join(imgtInputPath, befundFilename)
befundWriter = open(befundWritePath, "w")
befundWriter.write(befund)
befundWriter.close()

cellLinePatientFile = form["cellLinePatientFile"]
cellLinePatientFilename = cellLinePatientFile.filename
cellLinePatient = cellLinePatientFile.file.read()

cellLinePatientWritePath = path.join(imgtInputPath, cellLinePatientFilename)
cellLinePatientWriter = open(cellLinePatientWritePath, "w")
cellLinePatientWriter.write(cellLinePatient)
cellLinePatientWriter.close()

submissionId = form["submissionId"].value

imgtOutput_BaseLoc = "/downloads/imgtoutput"
imgtOutputPath = path.join(imgtOutput_BaseLoc, foldername)
discard = mkdir(imgtOutputPath)

imgtOutputZipFile = write_imgt_files(enaEmailWritePath, befundWritePath, cellLinePatientWritePath, submissionId, imgtOutputPath, enaFilesPath)

print imgtdownload % (imgtOutputZipFile, imgtOutputZipFile.split("/")[-1])
