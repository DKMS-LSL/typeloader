from imgtformat import *
import datetime
import re
from copy import copy
import textwrap

def make_genemodel_text(enaFile, sequence):
    
    enaHandle = open(enaFile)
    enaText = enaHandle.read()
    enaHandle.close()
    
    sequenceLength = len(sequence)
    
    # we are being very lazy here and working with the already generated FT lines format instead of recreating them from the gene model 
    gmodel_regex = re.compile("(((FT(.*?)(CDS(.*?)\n))((.*?)\n){5,6}))((((FT(.*?)exon((.*?)\n){4})(FT(.*?)intron((.*?)\n){4})){1,})((FT(.*?)exon((.*?)\n){4})))", re.MULTILINE)
    cdsText = gmodel_regex.search(enaText).expand("\\3")
    
    cdsStart = int(cdsText.split("..")[0].split("(")[1])
    cdsEnd = int(cdsText.split("..")[-1].split(")")[0])
    
    if cdsStart > 1: fiveUtrText = fiveUtrString.replace("{fiveUtrEnd}", str(cdsStart - 1))
    else: fiveUtrText = ""
    
    if cdsEnd < sequenceLength: threeUtrText = threeUtrString.replace("{threeUtrStart}",str(cdsEnd + 1)).replace("{threeUtrEnd}",str(sequenceLength))
    else: threeUtrText = ""
    
    enaExonIntronText = gmodel_regex.search(enaText).expand("\\9")
    if cdsStart > 1: enaExonIntronText = enaExonIntronText.replace(" 1..", " %s.." % str(cdsStart))
    if cdsEnd < sequenceLength: enaExonIntronText = enaExonIntronText.replace("..%s" % str(sequenceLength), "..%s" % str(cdsEnd))
    enaExonIntronLines = enaExonIntronText.strip().split("\n")
    imgtExonIntronLines = []
    
    for enaExonIntronLine in enaExonIntronLines:
        if (enaExonIntronLine.find("gene") != -1) or (enaExonIntronLine.find("allele") != -1): continue
        else: imgtExonIntronLines.append(enaExonIntronLine)
        
    imgtExonIntronText = "\n".join(imgtExonIntronLines)
    
    imgtGeneModelText = ""
    imgtGeneModelText += cdsText
    if len(fiveUtrText): imgtGeneModelText += "%s\n" % fiveUtrText
    imgtGeneModelText += "%s\n" % imgtExonIntronText
    if len(threeUtrText): imgtGeneModelText += "%s\n" % threeUtrText
    
    return imgtGeneModelText
    

def make_befund_text(befund, closestAllele):
    
    befundText = ""
    closestGene = closestAllele.split("*")[0].split("-")[1]
    
    for gene in befund.keys():
        
        if gene.startswith(closestGene): befund[gene].append("%snew" % closestAllele.split(":")[0].split("*")[1])
        
        alleles = ",".join([allele for allele in befund[gene] if allele.find("XXX") == -1])
        befundText += otherAllelesString.replace("{gene}", gene).replace("{alleleNames}",alleles)
    
    return befundText
        

def make_diff_line(differences, closestAllele):

    baseText = "%s differs from %s like so : "
    diffText = baseText % ("%s:new" % closestAllele.split(":")[0], closestAllele)
    
    diffsExist = False
    
   
    mm, mmPos, deltn, deltnPos, instn, instnPos = differences["mismatches"], differences["mismatchPositions"], \
                                                  differences["deletions"], differences["deletionPositions"], \
                                                  differences["insertions"], differences["insertionPositions"]
    
    mismatchText = ",".join(["pos %s (%s -> %s)" % (mmPos[mmIndex][1], mm[mmIndex][0], mm[mmIndex][1]) for mmIndex in range(len(mm))])
    if len(mismatchText):
        diffText += "Mismatches - %s. " % mismatchText
        diffsExist = True
        
    deletionText = ",".join(["pos %s (%s)" % (deltnPos[deltnIndex], deltn[deltnIndex]) for deltnIndex in range(len(deltn))])
    if len(deletionText):
        diffText += "Deletions = %s. " % deletionText
        diffsExist = True
        
    insertionText = ",".join(["pos %s (%s)" % (instnPos[instnIndex], instn[instnIndex]) for instnIndex in range(len(instn))])
    if len(insertionText):
        diffText += "Deletions = %s. " % insertionText
        diffsExist = True
        
    if diffsExist: return diffText
    else: return ""
    
def make_imgt_footer(sequence, sequencewidth=60): 

  
    footerop = footer.replace("{sequence length}",str(len(sequence)))
    footerop = footerop.replace("{countA}",str(sequence.count("A")))
    footerop = footerop.replace("{countG}",str(sequence.count("G")))
    footerop = footerop.replace("{countT}",str(sequence.count("T")))
    footerop = footerop.replace("{countC}",str(sequence.count("C")))
    
    tempseq = copy(sequence)
    tempseq = tempseq.replace("A","").replace("G","").replace("T","").replace("C","")
    othercount = len(tempseq)
    
    footerop = footerop.replace("{countOther}", str(othercount))
    
    seqlines = textwrap.wrap(sequence,sequencewidth)
    seqstring = ""
    
    padspace = " " * 5
    
    count = 0
    for seqline in seqlines:
        count += 60
        if len(seqline) < 60:
            sepbases = 5 - (len(seqline) / 10)
            nobases = 60 - len(seqline)
            currseq = " ".join(textwrap.wrap(seqline,10))
            currseqstring = padspace + currseq + (" " * (sepbases + nobases)) + padspace + str(len(sequence))
        else:
            currseq = " ".join(textwrap.wrap(seqline,10))
            currseqstring = padspace + currseq + padspace + str(count) + "\n"
        seqstring += currseqstring

    footerop = footerop.replace("{sequence}", seqstring)
    
    return footerop
    

def make_imgt_text(submissionId, cellLine, enaId, befund, closestAllele, diffToClosest, enafile, sequence):
    
    differencesText = refAlleleDiffString.replace("{text}",make_diff_line(diffToClosest,closestAllele))
    otherAllelesText = make_befund_text(befund, closestAllele)
    genemodelText = make_genemodel_text(enafile, sequence)
    footerText = make_imgt_footer(sequence)
    todaystr = datetime.datetime.now().strftime('%d/%m/%Y')
    
    imgtText = header
    imgtText = imgtText.replace("{submission_id}", submissionId)
    imgtText = imgtText.replace("{sequence length}", str(len(sequence)))
    imgtText = imgtText.replace("{allele_counter}", "1")
    imgtText = imgtText.replace("{submission_date}", todaystr)
    imgtText = imgtText.replace("{release_date}", todaystr)
    imgtText = imgtText.replace("{cell_line}", cellLine)
    imgtText = imgtText.replace("{refallele_diffs}", differencesText)
    imgtText = imgtText.replace("{ena_id}", enaId)
    imgtText = imgtText.replace("{other_alleles}", otherAllelesText)
    imgtText = imgtText.replace("{related allele}", closestAllele)
    
    imgtText += genemodelText
    imgtText += footerText
    
    return imgtText

    
    
    
    
    
    
    
    

