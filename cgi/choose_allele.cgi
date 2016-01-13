#!/usr/bin/python

from template import mainhtml
from coordinates import getCoordinates
from backend_make_ena import *

import time
import cgi


form = cgi.FieldStorage()

blastXmlFilename = form["xmlfilename"].value
annotations = getCoordinates(blastXmlFilename)


posHash = {}
sequences = {}
for genDxAllele in annotations.keys():
    posHash[genDxAllele] = {"utr":[],"exons":[],"introns":[]}
    features, coordinates, sequence = annotations[genDxAllele]["features"], annotations[genDxAllele]["coordinates"], annotations[genDxAllele]["sequence"]

    for featureIndex in range(len(features)):
        feature = features[featureIndex]
        if feature == "utr5" or feature == "utr3": posHash[genDxAllele]["utr"].append(coordinates[featureIndex])
        elif feature[1] == "e": posHash[genDxAllele]["exons"].append(coordinates[featureIndex])
        else: posHash[genDxAllele]["introns"].append(coordinates[featureIndex])

    sequences[genDxAllele] = sequence

dldfilename = "DKMS-LSL-"
ena1_text = ""
ena2_text = ""

cellLine1Alpha = ""
cellLine2Alpha = ""

if form.has_key("allele1") or form.has_key("both"):
    geneName = form["allele1_genename"].value
    newAlleleName = form["allele1_allelename"].value
    productName = form["allele1_product"].value
    cellLine = form["allele1_cellline"].value

    fromExon = int(form["allele1_fromexon"].value)
    toExon = int(form["allele1_toexon"].value)
    
    alleleName = form["allele1name"].value


    currentPosHash = posHash[alleleName]
    sequence = sequences[alleleName]
    enaPosHash = transform(currentPosHash)
    
    generalData = make_globaldata(gene=geneName,allele=newAlleleName,product=productName,species="Homo sapiens",seqLen=str(len(sequence)),cellline=cellLine)

    ena1_text = make_header(header, generalData, enaPosHash) + make_genemodel(exonString, intronString, generalData, enaPosHash, fromExon, toExon) + make_footer(footer, sequence)
    
    cellLine1Alpha = cellLine.strip().split("-")[-2]
    cellLine1Num = cellLine.strip().split("-")[-1]
    dldfilename += cellLine1Alpha + "-" + cellLine1Num
    

if form.has_key("allele2") or form.has_key("both"):
    geneName = form["allele2_genename"].value
    newAlleleName = form["allele2_allelename"].value
    productName = form["allele2_product"].value
    cellLine = form["allele2_cellline"].value

    fromExon = int(form["allele2_fromexon"].value)
    toExon = int(form["allele2_toexon"].value)
    
    alleleName = form["allele2name"].value


    currentPosHash = posHash[alleleName]
    sequence = sequences[alleleName]
    enaPosHash = transform(currentPosHash)
   
    generalData = make_globaldata(gene=geneName,allele=newAlleleName,product=productName,species="Homo sapiens",seqLen=str(len(sequence)),cellline=cellLine)

    ena2_text = make_header(header, generalData, enaPosHash) + make_genemodel(exonString, intronString, generalData, enaPosHash, fromExon, toExon) + make_footer(footer, sequence)
    
    cellLine2Alpha = cellLine.strip().split("-")[-2]
    cellLine2Num = cellLine.strip().split("-")[-1]
    
    if cellLine2Alpha == cellLine1Alpha:
        dldfilename += "_%s" % cellLine2Num
    elif len(cellLine1Alpha): dldfilename += "_%s-%s" % (cellLine2Alpha, cellLine2Num)
    else: dldfilename += "%s-%s"  % (cellLine2Alpha, cellLine2Num)
    
    
ena_text = ena1_text + ena2_text
dldfilename += ".txt"



  

dldfile = open("/downloads/enafiles/%s" % dldfilename, "w")
dldfile.write(ena_text)
dldfile.close()
   
    
ena_html = mainhtml % (newAlleleName, ena_text, dldfilename)
print ena_html
