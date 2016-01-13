#!/usr/bin/python

from template import mainhtml, allelechooser
from getAlleleSeqsAndBlast import blastGenDXSeqs
from closestallele import getClosestKnownAlleles


import cgi
import time

form = cgi.FieldStorage()
xmlFile = form["xmlFile"]
xmlFileName = xmlFile.filename
xmlText = xmlFile.file.read().replace("\r","\n")

genDxXmlFilename = "/downloads/xmlfiles/%s" % xmlFileName
uploadfile = open(genDxXmlFilename,"w")
uploadfile.write(xmlText)
uploadfile.close()

blastXmlFile = blastGenDXSeqs(genDxXmlFilename)
closestAlleles = getClosestKnownAlleles(blastXmlFile)

genDxAlleleNames = closestAlleles.keys()
closestAlleleNames = [closestAlleles[genDxAlleleName]["name"] for genDxAlleleName in genDxAlleleNames]

geneNames = [alleleName.split("*")[0] for alleleName in genDxAlleleNames]
alleleNames = ["%s:new" % alleleName.split(":")[0] for alleleName in closestAlleleNames]

products = []
for geneName in geneNames:
    if geneName.startswith("D"): products.append("MHC class II antigen")
    else: products.append("MHC class I antigen")

chooser_html = allelechooser % (blastXmlFile, genDxAlleleNames[0], closestAlleleNames[0], genDxAlleleNames[0], closestAlleleNames[0], \
                                geneNames[0], geneNames[0], alleleNames[0], alleleNames[0], products[0], products[0], \
                                genDxAlleleNames[1], closestAlleleNames[1], genDxAlleleNames[1], closestAlleleNames[1], \
                                geneNames[1], geneNames[1], alleleNames[1], alleleNames[1], products[1], products[1])
print chooser_html
    




