#!/usr/bin/env python

import datetime
import re
from copy import copy
import textwrap
if __name__ == '__main__':
    from imgtformat import *
    from errors import BothAllelesNovelError, InvalidPretypingError
else:    
    from .imgtformat import *
    from .errors import BothAllelesNovelError, InvalidPretypingError

def make_genemodel_text(enaFile, sequence, partial_UTR5, partial_UTR3):
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

    if cdsStart > 1: 
        fiveUtrText = fiveUtrString.replace("{fiveUtrEnd}", str(cdsStart - 1))
        if partial_UTR5:
            fiveUtrText += "\nFT                  \partial"
    else: 
        fiveUtrText = ""

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
    if len(threeUtrText): 
        imgtGeneModelText += "%s\n" % threeUtrText
        if partial_UTR3:
            imgtGeneModelText += "FT                  \partial\n"

    return imgtGeneModelText


def reformat_partner_allele(alleles, myallele, length, delimiter, log):
    """tries to figure out which of the two novel alleles of the target locus is itself
    """
    log.info("Figuring out which allele this is...")
    if "*" in myallele.target_allele:
        myself = myallele.target_allele.split("*")[1]
    else:
        myself = myallele.target_allele
    success = False
    for i in range(len(alleles)):
        if alleles[i] == myself:
            match = True
            for j in range(len(alleles)):
                if i != j:
                    if not alleles[j].split(":")[0] in myallele.partner_allele:
                        match = False
            if match: # if all remaining alleles are part of myallele.partner_allele
                partners = []
                for k, a in enumerate(alleles):
                    if k != i:
                        if ":" in a:
                            partners.append(a.split(":")[0])
                        else:
                            partners.append(a[:length])
                partner = delimiter.join(partners)
                reformated_alleles = [alleles[i], partner]
                appendix = "s are" if len(alleles) > 2 else " is"
                log.info("\t => Success: {} is self, partner allele{} {}!".format(alleles[i], appendix, 
                                                                                  partner))
                success = True
                continue
                        
    if success:
        alleles = reformated_alleles

    else:
        log.info("\t => Could not figure it out, need user input!")
    alleles = delimiter.join(alleles)
    return success, alleles


def check_all_required_loci(befund_text, gene, target_allele, alleles, allele_name, log):
    """makes sure all loci required by IPD have a pretyping
    """
    required = ["HLA-A", "HLA-B", "HLA-DRB1", gene]
    missing = []
    for locus in required:
        if not locus in befund_text:
            missing.append(locus)
    if missing:
        log.warning("No pretyping found for {}. IPD requires at least HLA-A, -B, -DQB1 and the target gene of your novel allele!".format(",".join(missing)))
        raise InvalidPretypingError(target_allele, "", allele_name, gene, 
                                    "pretyping for {} missing".format(" and ".join(sorted(missing))))
        
    
def make_befund_text(befund, self_name, myallele, closestAllele, geneMap, differencesText, log):
#     print("befund = ", befund)
#     print("self_name =", self_name)
#     print("myallele =", myallele)
#     print("closestAllele =", closestAllele)
#     print("geneMap =", geneMap)
#     print("differencesText = ", differencesText)
    befundText = ""
    alleles = []
    confirmation = False
    if differencesText.startswith("CC   Confirmation"):
        confirmation = True
        
    for gene in list(befund.keys()):
        genesystem = gene[:3]
        length = None
        delimiter = ","
        if genesystem == "HLA":
            length = 2
        elif genesystem in ["KIR", "MIC"]:
            length = 3
            if genesystem == "KIR":
                delimiter = "+" # for KIR, use a plus as allele separator (normal GL strings)
        
        if length:
            myalleles = [allele.zfill(length) for allele in befund[gene]]
        else:
            myalleles = befund[gene]
        alleles = delimiter.join(myalleles)
        
        if not gene.startswith("KIR"):
            if "|" in alleles:
                raise InvalidPretypingError(myallele, myalleles, "", gene, "Pretyping contains '|'! GL-Strings are only accepted for KIR!")
         
        if gene == myallele.gene:
            # check for consistency:
            mystring = alleles.lower()
            if "pos" in mystring: # target locus not allowed to be POS
                log.warning("Invalid Pretyping: pretyping for target locus should not contain POS. Please adjust pretyping file!")
                raise InvalidPretypingError(myallele, myalleles, self_name, gene, "POS is not acceptable pretyping for a target locus")
                return
                
            i = mystring.count("new") + mystring.count("xxx")
            if i == 0: # no pretyping marked as new
                if not confirmation:
                    raise InvalidPretypingError(myallele, myalleles, self_name, gene, "no allele marked as new in pretyping")
                    return
                
            if i > 1:
                log.info("Target locus {} has {} novel alleles".format(myallele.gene, i))
                success, alleles = reformat_partner_allele(myalleles, myallele, length, delimiter, log)
                if not success:
                    log.warning("Please indicate self!".format(myallele.gene, i))
                    raise BothAllelesNovelError(myallele, myalleles)
                    return
                
            else:
                if self_name.replace(":new", "").replace("new","") not in mystring:
                    log.warning("Invalid Pretyping: allele_name '{}:new' not found in pretyping for target locus. Please adjust pretyping file!".format(self_name))
                    raise InvalidPretypingError(myallele, myalleles, self_name, gene,
                                                "assigned allele name not found in pretyping")
                    return
            
            if confirmation:
                alleles = alleles.replace(self_name, closestAllele.split("*")[1])
        
        befundText += otherAllelesString.replace("{gene}", gene).replace("{alleleNames}", alleles)
    check_all_required_loci(befundText, myallele.gene, myallele, alleles, self_name, log)
    return befundText


def make_diff_line(differences, imgtDiff, self_name, closestAllele):

    baseText = "%s differs from %s like so : "
    diffText = baseText % (self_name, closestAllele)

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
    else: 
        return "Confirmation of {}".format(closestAllele)

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


def make_imgt_text(submissionId, cellLine, local_name, myallele, enaId, befund, closestAllele, diffToClosest, 
                   imgtDiff, enafile, sequence, geneMap, missing_bp_start, missing_bp_end,
                   settings, log):
    
    [locus, self_name] = closestAllele.split("*")
    if locus.startswith("KIR"):
        db_name = "KIR"
        self_name = self_name[:3] + "new"
    else:
        self_name = self_name.split(":")[0] + ":new"
        db_name = "HLA"

    diffLine = make_diff_line(diffToClosest, imgtDiff, "{}*{}".format(locus, self_name), closestAllele)
    differencesText = refAlleleDiffString.replace("{text}", diffLine)    
    otherAllelesText = make_befund_text(befund, self_name, myallele, closestAllele, geneMap, differencesText, log)
    
    partial_UTR5, partial_UTR3 = False, False
    if missing_bp_start:
        partial_UTR5 = True
    if missing_bp_end:
        partial_UTR3 = True
        
    genemodelText = make_genemodel_text(enafile, sequence, partial_UTR5, partial_UTR3)
    footerText = make_imgt_footer(sequence)
    todaystr = datetime.datetime.now().strftime('%d/%m/%Y')

    imgtText = header
    
    # reformat names & emails for presence or absence of optional parts:
    user_name = settings["user_name"]
    if settings["address_form"]:
        user_name = settings["address_form"] + " " + user_name
    lab_contact = settings["lab_contact"]
    if settings["lab_contact_address"]:
        lab_contact = settings["lab_contact_address"] + " " + lab_contact
    emails = settings["lab_contact_email"]
    if settings["email"]:
        emails = settings["email"] + "," + emails
    
    replace_placeholders = [("{submission_id}", submissionId),
                            ("{sequence length}", str(len(sequence))),
                            ("{allele_counter}", "1"),
                            ("{submission_date}", todaystr),
                            ("{release_date}", todaystr),
                            ("{cell_line}", cellLine),
                            ("{local_name}", local_name),
                            ("{refallele_diffs}", differencesText),
                            ("{ena_id}", enaId),
                            ("{other_alleles}", otherAllelesText),
                            ("{related allele}", closestAllele),
                            ("{submittor id}", settings["submittor_id"]),
                            ("{address form}", settings["address_form"]),
                            ("{full user name}", user_name),
                            ("{lab contact}", lab_contact),
                            ("{email}", emails),
                            ("{lab of origin}", settings["lab_of_origin"]),
                            ("{material available}", settings["material_available"]),
                            ("{typeloader version}", settings["TL_version"]),
                            ("{database}", db_name),
                            ("{db version}", settings["db_versions"][db_name]),
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

if __name__ == '__main__':
    import logging
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s [%(asctime)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)
    
    from collections import namedtuple
    befund =  {'HLA-A': ['01:02|24:02:01G', '02:01:01G'], 'HLA-B': ['39:06:02G', '48:01:01G'], 'HLA-C': ['08:01:01G', '07:02:01G'], 'HLA-DRB1': ['08:02:01G', '14:06:01'], 'HLA-DQB1': ['04:02', '03:01:01'], 'HLA-DPB1': ['04:02', '04:02'], 'HLA-E': ['01:01:01G', '01:03:01G'], 'MICB': ['004:new', '005:new']}
    self_name = "004:new"
    closestAllele = "MICB*004:01:01"
    TargetAllele = namedtuple("TargetAllele", "gene target_allele partner_allele")
    myallele = TargetAllele(gene='MICB', target_allele='MICB*004:new', partner_allele='MICB*005:new')
    geneMap =  {'gene': ['HLA', 'KIR'], 'targetFamily': 'HLA'}
    differencesText =  "CC   MICB*004:new differs from MICB*004:01:01 like so : [...]" 

    make_befund_text(befund, self_name, myallele, closestAllele, geneMap, differencesText, log)
