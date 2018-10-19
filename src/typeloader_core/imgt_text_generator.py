from .imgtformat import *
import datetime
import re
from copy import copy
import textwrap

def make_genemodel_text(enaFile, sequence):

    enaHandle = open(enaFile)
    enaText = enaHandle.read().replace("\r","\n").replace("\n\n","\n")
    enaHandle.close()

    sequenceLength = len(sequence)

    # we are being very lazy here and working with the already generated FT lines format instead of recreating them from the gene model
    gmodel_regex = re.compile("(((FT(.*?)(CDS(.*?)\n))((.*?)\n){5,6}))(((FT(.*?)(exon|intron)((.*?)\n){4,5}){1,})((FT(.*?)exon((.*?)\n){4})))", re.MULTILINE)

    cdsText = gmodel_regex.search(enaText).expand("\\3")
    cdsText = cdsText.replace("             ","            ")

    cdsStart = int(cdsText.split("..")[0].split("(")[1])
    cdsEnd = int(cdsText.split("..")[-1].split(")")[0])

    if cdsStart > 1: fiveUtrText = fiveUtrString.replace("{fiveUtrEnd}", str(cdsStart - 1))
    else: fiveUtrText = ""

    if cdsEnd < sequenceLength: threeUtrText = threeUtrString.replace("{threeUtrStart}",str(cdsEnd + 1)).replace("{threeUtrEnd}",str(sequenceLength))
    else: threeUtrText = ""

    enaExonIntronText = gmodel_regex.search(enaText).expand("\\9")
    enaExonIntronText = enaExonIntronText.replace("/p","\\p").replace("/n","\\n").replace("exon","Exon").replace("intron","Intron")
    if cdsStart > 1: enaExonIntronText = enaExonIntronText.replace(" 1..", " %s.." % str(cdsStart))
    if cdsEnd < sequenceLength: enaExonIntronText = enaExonIntronText.replace("..%s" % str(sequenceLength), "..%s" % str(cdsEnd))
    enaExonIntronLines = enaExonIntronText.strip().split("\n")
    imgtExonIntronLines = []

    for enaExonIntronLine in enaExonIntronLines:
        if (enaExonIntronLine.find("gene") != -1) or (enaExonIntronLine.find("allele") != -1): continue
        else:
            if enaExonIntronLine.find("number") != -1:
                lineParts = enaExonIntronLine.split("=")
                newExonIntronLine = lineParts[0] + "=\"" + lineParts[1].strip() + "\""
                imgtExonIntronLines.append(newExonIntronLine)
            else:
                imgtExonIntronLines.append(enaExonIntronLine)

    imgtExonIntronText = "\n".join([imgtExonIntronLine.replace("          ","         ").replace("            ","           ") \
                                    for imgtExonIntronLine in imgtExonIntronLines])

    imgtGeneModelText = ""
    imgtGeneModelText += cdsText
    if len(fiveUtrText): imgtGeneModelText += "%s\n" % fiveUtrText
    imgtGeneModelText += "%s\n" % (imgtExonIntronText.replace("\\"," \\"))
    if len(threeUtrText): imgtGeneModelText += "%s\n" % threeUtrText

    return imgtGeneModelText


def make_befund_text(befund, closestAllele, geneMap):

    befundText = ""

    for gene in list(befund.keys()):
        if (re.search(geneMap["gene"][0], gene) and geneMap["targetFamily"] == geneMap["gene"][0] or geneMap["targetFamily"] == geneMap["gene"][1]):
            alleles = ",".join([allele for allele in befund[gene] if allele.find("XXX") == -1])
            befundText += otherAllelesString.replace("{gene}", gene).replace("{alleleNames}",alleles)
    return befundText


def make_diff_line(differences, imgtDiff, closestAllele):

    baseText = "%s differs from %s like so : "
    diffText = baseText % ("%s:new" % closestAllele.split(":")[0], closestAllele)

    diffsExist = False


    mm, mmPos, deltn, deltnPos, instn, instnPos = differences["mismatches"], imgtDiff["mismatchPositions"], \
                                                  differences["deletions"], differences["deletionPositions"], \
                                                  differences["insertions"], differences["insertionPositions"]

    codonDiff = imgtDiff["mmCodons"]


    mismatchText = ""
    for mmIndex in range(len(mm)):
        mismatchPos, codonStatus = mmPos[mmIndex]
        if not codonStatus: mismatchText += "pos %s (%s -> %s);" % (mmPos[mmIndex][0], mm[mmIndex][1], mm[mmIndex][0])
        else:

            mismatchText += "pos %s in codon %s (%s -> %s);" % \
                            (mmPos[mmIndex][0], codonDiff[mmIndex][0], codonDiff[mmIndex][1][1], codonDiff[mmIndex][1][0])

    if len(mismatchText):
        diffText += "Mismatches = %s. " % mismatchText
        diffsExist = True

    deletionText = ",".join(["pos %s (%s)" % (deltnPos[deltnIndex], deltn[deltnIndex]) for deltnIndex in range(len(deltn))])
    if len(deletionText):
        diffText += "Deletions = %s. " % deletionText
        diffsExist = True

    insertionText = ",".join(["pos %s (%s)" % (instnPos[instnIndex], instn[instnIndex]) for instnIndex in range(len(instn))])
    if len(insertionText):
        diffText += "Insertions = %s. " % insertionText
        diffsExist = True

    if diffsExist: return diffText
    else: return "Confirmation"

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
            sepbases = 5 - (len(seqline) // 10)
            nobases = 60 - len(seqline)
            currseq = " ".join(textwrap.wrap(seqline,10))
            currseqstring = padspace + currseq + (" " * (sepbases + nobases)) + padspace + str(len(sequence))
        else:
            currseq = " ".join(textwrap.wrap(seqline,10))
            currseqstring = padspace + currseq + padspace + str(count) + "\n"
        seqstring += currseqstring.lower()

    footerop = footerop.replace("{sequence}", seqstring)

    return footerop


def make_imgt_text(submissionId, cellLine, enaId, befund, closestAllele, diffToClosest, 
                   imgtDiff, enafile, sequence, geneMap, settings):

    differencesText = refAlleleDiffString.replace("{text}",make_diff_line(diffToClosest, imgtDiff, closestAllele))
    otherAllelesText = make_befund_text(befund, closestAllele, geneMap)
    genemodelText = make_genemodel_text(enafile, sequence)
    footerText = make_imgt_footer(sequence)
    todaystr = datetime.datetime.now().strftime('%d/%m/%Y')

    imgtText = header
    replace_placeholders = [("{submission_id}", submissionId),
                            ("{sequence length}", str(len(sequence))),
                            ("{allele_counter}", "1"),
                            ("{submission_date}", todaystr),
                            ("{release_date}", todaystr),
                            ("{cell_line}", cellLine),
                            ("{refallele_diffs}", differencesText),
                            ("{ena_id}", enaId),
                            ("{other_alleles}", otherAllelesText),
                            ("{related allele}", closestAllele),
                            ("{submittor id}", settings["submittor_id"]),
                            ("{address form}", settings["address_form"]),
                            ("{full user name}", settings["user_name"]),
                            ("{contact address form}", settings["lab_contact_address"]),
                            ("{lab contact}", settings["lab_contact"]),
                            ("{user email}", settings["email"]),
                            ("{lab contact email}", settings["lab_contact_email"]),
                            ("{lab of origin}", settings["lab_of_origin"]),
                            ("{material available}", settings["material_available"]),
                            ("{typeloader version}", settings["TL_version"]),
                            ("{primary sequencing tech}", settings["primary_sequencing"]),
                            ("{secondary sequencing tech}", settings["secondary_sequencing"]),
                            ("{type of primer}", settings["type_of_primer"]),
                            ("{sequenced in isolation}", settings["sequenced_in_isolation"]),
                            ("{no of reactions}", settings["no_of_reactions"]),
                            ("{sequencing directions}", settings["sequencing_direction"]),
                            ("{confirmation methods}", settings["confirmation_methods"])
                            ]
    for (placeholder, replacement) in replace_placeholders:
        imgtText = imgtText.replace(placeholder, replacement)
    
    imgtText += genemodelText
    imgtText += footerText

    return imgtText
