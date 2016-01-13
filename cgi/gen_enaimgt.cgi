#!/usr/bin/python

import cgi
from template import mainhtml_temp, allelechooser
from backend_make_ena import *
from backend_make_imgt import *
from backend_xmlfuncs import *
import time

form = cgi.FieldStorage()
xmlFile = form["xmlFile"]
xmlFileName = xmlFile.filename
xmlText = xmlFile.file.read().replace("\r","\n")


geneName = form["genename"].value
newAlleleName = form["allelename"].value
productName = form["product"].value
cellLine = form["cellline"].value
imgtsubmissionid = form["subid"].value


fromExon = int(form["fromexon"].value)
toExon = int(form["toexon"].value)

imgtmm_pos = int(form["mmpos"].value)
imgtmm_base = form["oldbase"].value
imgtnew_base = form["newbase"].value
oldcodonseq = form["oldcodon"].value
newcodonseq = form["newcodon"].value

xmlData = parseXML(xmlText)
alleleNames = getAlleleName(xmlData)
if len(alleleNames) == 1:
    alleleName = alleleNames[0]
    haplotypes = getHaplotypeIds(xmlData, alleleName)
    sequence = sequenceFromHaplotype(xmlData, haplotypes)
    posHash = getCoords(xmlData)
    enaPosHash = transform(posHash)
    
    generalData = make_globaldata(gene=geneName,allele=newAlleleName,product=productName,species="Homo sapiens",seqLen=str(len(sequence)),cellline=cellLine)
    ena_text = make_header(header, generalData, enaPosHash) + make_genemodel(exonString, intronString, generalData, enaPosHash, fromExon, toExon) + make_footer(footer, sequence)
    
    imgtGeneralData = make_imgtglobaldata(submission_id=imgtsubmissionid,allele_counter=1,sequencelength=len(sequence),relatedallele=alleleName,allelename=newAlleleName,gene=geneName)
    
    imgt_header = make_imgtheader(imgtheader,imgtGeneralData,posHash,enaPosHash,mm_pos=imgtmm_pos,mm_base=imgtmm_base,new_base=imgtnew_base, mm_codon=oldcodonseq,new_codon=newcodonseq)
    imgt_genemodel = make_imgtgenemodel(imgtexonString,imgtintronString,imgtGeneralData,enaPosHash, fromExon, toExon)
    imgt_footer = make_imgtfooter(imgtfooter, sequence)
    imgt_text = imgt_header + imgt_genemodel + imgt_footer

    dldfile = open("/downloads/enafiles/%s_%s.ena.txt" % (newAlleleName,time.strftime("%d_%m_%Y-%H_%M_%S")), "w")
    dldfile.write(ena_text)
    dldfile.close()
    
    dldfile = open("/downloads/imgtfiles/%s_%s.imgt.txt" % (newAlleleName,time.strftime("%d_%m_%Y-%H_%M_%S")), "w")
    dldfile.write(imgt_text)
    dldfile.close()

    ena_html = mainhtml_temp % (newAlleleName, ena_text, imgt_text, "%s_%s.ena.txt" % (newAlleleName,time.strftime("%d_%m_%Y-%H_%M_%S")), \
                                "%s_%s.imgt.txt" % (newAlleleName,time.strftime("%d_%m_%Y-%H_%M_%S")))
    print ena_html
else:
    uploadfile = open("/downloads/xmlfiles/%s" % xmlFileName,"w")
    uploadfile.write(xmlText)
    uploadfile.close()
    
    chooser_html = allelechooser % (xmlFileName, alleleNames[0], alleleNames[0], alleleNames[1], alleleNames[1])
    print chooser_html
    
    




