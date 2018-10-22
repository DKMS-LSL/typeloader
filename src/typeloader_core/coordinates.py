# This routine establishes the co-ordinates for the new allele from the closest known allele
# The closest known allele is determined using getclosestKnownAllele from closestallele.py


import re
from Bio import SeqIO
from .closestallele import getClosestKnownAlleles
from .hla_embl_parser import read_dat_file
from .imgtTransform import changeToImgtCoords

from copy import copy
from math import ceil, floor
from pickle import load
from sys import argv

def getSpecificCodonChords(closestallele, exon1Length):

    if any(re.findall(r'KIR2DL1|KIR2DL2|KIR2DL3|KIR2DL5|KIR3DP1|KIR2DS|KIR3DL|KIR2DP|KIR3DP|', closestallele, re.IGNORECASE)):
        numExon1Coords = 21
    elif "KIR2DL4" in closestallele:
        numExon1Coords = 23
    else:
        numExon1Coords = int(floor(float(exon1Length)/3))

    return numExon1Coords


def getMismatchData(annotations):

    cdsMap = annotations["cdsMap"]
    alleleSeq = annotations["sequence"]
    closestallele = annotations["closestAllele"]

    # changed old statement to generate closestAlleleCdsSeq,
    # because pseudoexons could be in KIR
    closestAlleleCdsSeq = annotations["closestAlleleCdsSequence"]

    genomicExonCoords = list(cdsMap.keys())
    genomicExonCoords.sort()

    cdsExonCoords = [cdsMap[genomicExonCoord] for genomicExonCoord in genomicExonCoords]

    cdsSeq = "".join([alleleSeq[(start-1):end] for (start,end) in genomicExonCoords])

    mmCodons = []

    exon1Length = cdsExonCoords[0][1]
    numExon1Coords = getSpecificCodonChords(closestallele, exon1Length)

    for mmIndex in range(len(annotations["differences"]["mismatches"])):
        genomicPos, cdsPos = annotations["differences"]["mismatchPositions"][mmIndex], \
                             annotations["imgtDifferences"]["mismatchPositions"][mmIndex][0]

        if genomicPos == cdsPos:
            mmCodons.append(())
            continue

        canonicalMMCodonNum = int(ceil(float(cdsPos)/3))

        """
        # older version which was got class I codon assignments correct, and class II assignments wrong
        # IMGT assigns the first codon in exon 2 as codon 1, and the codons in exon 1 with a -1 backwards
        if canonicalMMCodonNum > numExon1Coords: imgtMMCodonNum = canonicalMMCodonNum - numExon1Coords
        else: imgtMMCodonNum = canonicalMMCodonNum - (numExon1Coords + 1)
        """

        """
        The first codon per IMGT definition corresponds to the start of the mature protein
        For class I, this is exon 2, and for class II, this is exon 1
        """
 
        if closestallele.find("DPB1") != -1: imgtMMCodonNum = canonicalMMCodonNum
        else:
            if canonicalMMCodonNum > numExon1Coords: imgtMMCodonNum = canonicalMMCodonNum - numExon1Coords
            else: imgtMMCodonNum = canonicalMMCodonNum - (numExon1Coords + 1)

        """
        Getting rid of the codon sequence madness, sort of bruting it

        #for pos in range(cdsPos - 3,cdsPos + 3):
        #    if pos == cdsPos: isCdsPos = "*"
        #    else: isCdsPos = ""
        #    #print "%s\t%s\t%s\t%s\t%s" % (pos, closestAlleleCdsSeq[pos], cdsSeq[pos], pos + 1, isCdsPos)
        ##print "-" * 10

        #cdsPos -= 1
        if not (cdsPos % 3):# coords stored are 1-based, python indices are 0-based
            #cdsPos += 1
            actualCodonSeq, closestCodonSeq = cdsSeq[cdsPos - 1  : cdsPos + 2 ], closestAlleleCdsSeq[cdsPos - 1 : cdsPos + 2] #
        elif (cdsPos % 3) == 2:
            #cdsPos += 1
            actualCodonSeq, closestCodonSeq = cdsSeq[cdsPos : cdsPos + 3], closestAlleleCdsSeq[cdsPos : cdsPos + 3]
        else:
            #cdsPos += 1
            actualCodonSeq, closestCodonSeq = cdsSeq[cdsPos - 2 : cdsPos + 1], closestAlleleCdsSeq[cdsPos - 2  : cdsPos + 1]
        """

        cdsCodonHash, closestAlleleCodonHash = {},{}
        startPos = 0

        for index in range(1,(len(cdsSeq)//3) + 1):
            cdsCodonHash[index], closestAlleleCodonHash[index] = cdsSeq[startPos:startPos+3], closestAlleleCdsSeq[startPos:startPos+3]
            startPos += 3

        if cdsCodonHash[canonicalMMCodonNum] != closestAlleleCodonHash[canonicalMMCodonNum]:
            mmCodons.append((imgtMMCodonNum,(cdsCodonHash[canonicalMMCodonNum], closestAlleleCodonHash[canonicalMMCodonNum])))
        elif cdsCodonHash[canonicalMMCodonNum - 1] != closestAlleleCodonHash[canonicalMMCodonNum - 1]:
            mmCodons.append((imgtMMCodonNum,  (cdsCodonHash[canonicalMMCodonNum - 1], closestAlleleCodonHash[canonicalMMCodonNum - 1])))
        else:
            mmCodons.append((imgtMMCodonNum,  (cdsCodonHash[canonicalMMCodonNum + 1], closestAlleleCodonHash[canonicalMMCodonNum + 1])))

    return mmCodons


def getCoordinates(blastXmlFilename, allelesFilename, targetFamily, settings, log, isENA=True):

    allAlleles = read_dat_file(allelesFilename, targetFamily, isENA)
    closestAlleles = getClosestKnownAlleles(blastXmlFilename, targetFamily, settings, log)

    seqsFile = blastXmlFilename.replace(".blast.xml",".fa")

    try: 
        seqsHandle = open(seqsFile)
    except IOError:
        seqsFile = blastXmlFilename.replace(".blast.xml",".fasta")
        seqsHandle = open(seqsFile)

    seqsHash = SeqIO.to_dict(SeqIO.parse(seqsHandle, "fasta"))
    annotations = processAlleles(closestAlleles, allAlleles, seqsHash)

    for gendxAllele in list(annotations.keys()):
        if annotations[gendxAllele] == None: continue
        alleleSeq = str(seqsHash[gendxAllele].seq)
        annotations[gendxAllele]["sequence"] = alleleSeq
        annotations[gendxAllele]["imgtDifferences"]["mmCodons"] = getMismatchData(annotations[gendxAllele])

    seqsHandle.close()

    return annotations

def processAlleles(closestAlleles, allAlleles, hashOfQuerySequences):

    annotations = {}
    for alleleQuery in  list(closestAlleles.keys()):
        if not closestAlleles[alleleQuery]:
            annotations[alleleQuery] = None
            continue
        closestAlleleName, differences, isExactMatch, concatHSPS = closestAlleles[alleleQuery]["name"], closestAlleles[alleleQuery]["differences"], \
                                                                    closestAlleles[alleleQuery]["exactMatch"], closestAlleles[alleleQuery]["concatHSPS"]

        features, coordinates, extraInformation, closestAlleleCdsSequence, closestAlleleSequence = calculateCoordinates(closestAlleleName, allAlleles, differences, len(hashOfQuerySequences[alleleQuery]))
        utr5Length = len(allAlleles[closestAlleleName].UTR5)

        features, coordinates, imgtDifferences, cdsMap = changeToImgtCoords(features, coordinates, differences, utr5Length)

        annotations[alleleQuery] = {"features":features, "coordinates":coordinates, "imgtDifferences": imgtDifferences, "differences":differences, \
                                    "closestAllele":closestAlleleName, "cdsMap":cdsMap, "closestAlleleCdsSequence": closestAlleleCdsSequence, \
                                    "closestAlleleSequence":closestAlleleSequence, "isExactMatch":isExactMatch, "extraInformation":extraInformation, \
                                    "concatHSPS": concatHSPS}

    return annotations

def getClosestAlleleCoordinates(alleleData, queryLength):

    features = []
    coordinates = []
    exonIds = []
    extraInformation = {"pseudoexon":{}, "exon_number":{}, "intron_number":{}}
    closestAlleleCdsSequence = ""
    closestAlleleSequence = ""

    if "utr5" in alleleData.utrpos_dic:
        features.append("utr5")
        coordinates.append((alleleData.utrpos_dic["utr5"][0] + 1, alleleData.utrpos_dic["utr5"][1]))

    for exon, pseudoexon in alleleData.pseudo_exon_dic.items():
        extraInformation["pseudoexon"][exon] = pseudoexon
    for exon, exon_number in alleleData.exon_num_dic.items():
        extraInformation["exon_number"][exon] = exon_number
    for intron, intron_number in alleleData.intron_num_dic.items():
        extraInformation["intron_number"][intron] = intron_number

    #exonIds = [(exonNumber,"e") for exonNumber in alleleData.exonpos_dic.keys()]
    for exonNumber in list(alleleData.exonpos_dic.keys()):
        #print extraInformation["pseudoexon"][exonNumber]
        if extraInformation["pseudoexon"][exonNumber]:
            exonIds.append((exonNumber, "epseudo"))
        else:
            exonIds.append((exonNumber, "e"))

    intronIds = [(intronNumber, "i") for intronNumber in list(alleleData.intronpos_dic.keys())]

    cdsIds = copy(exonIds)
    cdsIds.extend(intronIds)
    cdsIds.sort()
    features.extend(cdsIds)

    for cdsId in cdsIds:
        if cdsId[1] == "e":
            coordinates.append((alleleData.exonpos_dic[cdsId[0]][0] + 1, alleleData.exonpos_dic[cdsId[0]][1]))
            closestAlleleCdsSequence += alleleData.seq[alleleData.exonpos_dic[cdsId[0]][0]:alleleData.exonpos_dic[cdsId[0]][1]]
        elif cdsId[1] == "epseudo":
            coordinates.append((alleleData.exonpos_dic[cdsId[0]][0] + 1, alleleData.exonpos_dic[cdsId[0]][1]))
        else: coordinates.append((alleleData.intronpos_dic[cdsId[0]][0] + 1, alleleData.intronpos_dic[cdsId[0]][1]))

    if "utr3" in alleleData.utrpos_dic:
        features.append("utr3")
        coordinates.append((alleleData.utrpos_dic["utr3"][0] + 1, queryLength))

    closestAlleleSequence = alleleData.seq

    return (features, coordinates, extraInformation, closestAlleleCdsSequence, closestAlleleSequence)

def calculateCoordinates(alleleName, alleles, differences, queryLength):

    allele = alleles[alleleName]
    features, coordinates, extraInformation, closestAlleleCdsSequence, closestAlleleSequence = getClosestAlleleCoordinates(allele, queryLength)

    #features = ['utr5', (1, 'e'), (1, 'i'), (2, 'e'), (2, 'i'), ... , 'utr3']
    #coordinates = [(1, 267), ... , (10737, 10561)]

    insertions, deletions, mismatches = differences["insertionPositions"], differences["deletionPositions"], \
                                        differences["mismatchPositions"]

    """
    The logic for assigning the co-ordinates for the new allele is quite complex. The steps are listed below :

    1. Iterate through the gene model features
    2. For each feature, check the number of insertions and deletions that lie within that feature
    3. (numInsertions - numDeletions) will be the change in the 3' end of that feature, even if an insertion or deletion is at the boundary
    4. If there are mismatches within that region, these are checked individually if they are before or after an insertion or deletion and changes made
    5. Every feature following that feature has its boundaries changed by (numInsertions - numDeletions)
    6. Every mismatch in every following feature is also changed by (numInsertions - numDeletions)

    Note : We take advantage of the fact that a list is mutable, but have to keep in mind tuples are not
    """

    #Step 1
    for coordIndex in range(len(coordinates)):
        #Step 2
        regionBegin, regionEnd = coordinates[coordIndex]
        regionInsertions = [insertion for insertion in insertions if ((insertion >= regionBegin) and (insertion <= regionEnd))]
        regionDeletions = [deletion for deletion in deletions if ((deletion >= regionBegin) and (deletion <= regionEnd))]

        coordChange = len(regionInsertions) - len(regionDeletions)

        if not coordChange: continue

        # Step 3
        if coordIndex != len(coordinates) - 1:
            coordinates[coordIndex] = (coordinates[coordIndex][0], coordinates[coordIndex][1]+coordChange)
        else:
            # no position pushing in the last iteration has to be done
            # start of 3' UTR was pushed already in step5, if there are insertions/deletions
            # end of 3' UTR = sequence length
            coordinates[coordIndex] = (coordinates[coordIndex][0], coordinates[coordIndex][1])

        #Step 4
        for mismatchIndex in range(len(mismatches)):
            mismatch = mismatches[mismatchIndex]
            if (mismatch >= regionBegin) and (mismatch <= regionEnd):
                for regionInsertion in regionInsertions:
                    if mismatch > regionInsertion: mismatches[mismatchIndex] += 1
                for regionDeletion in regionDeletions:
                    if mismatch > regionDeletion: mismatches[mismatchIndex] -= 1
            #Step 6
            if mismatch > regionEnd:
                mismatches[mismatchIndex] += coordChange

        #Step 5
        for nextFeatureIndex in range(coordIndex + 1, len(coordinates)):
            translated_region = (coordinates[nextFeatureIndex][0] + coordChange, coordinates[nextFeatureIndex][1] + coordChange)
            utr_end = coordinates[nextFeatureIndex] = (coordinates[nextFeatureIndex][0] + coordChange, coordinates[nextFeatureIndex][1])
            # push only the start of 3' UTR, if there are insertions/deletions
            # no entry if coordIndex + 1 = len(coordinates), see Step 3
            coordinates[nextFeatureIndex] = translated_region if nextFeatureIndex != len(coordinates) - 1 else utr_end

    return (features, coordinates, extraInformation, closestAlleleCdsSequence, closestAlleleSequence)

if __name__ == '__main__':

    t = getCoordinates(argv[1], argv[2], argv[3], isENA=True)
    #print t
    """
    from getAlleleSeqsAndBlast import blastSequences
    from sys import argv

    blastXmlFile = blastSequences(fastaFile)
    typeloaderOutput = getCoordinates(argv[1])

    typeloaderFile = argv[1].replace(".blast.xml",".typeloader.txt")
    typeloaderHandle = open(typeloaderFile,"w")

    for gendxAllele in typeloaderOutput.keys():
        typeloaderHandle.write("TypeLoader Query : %s\n" % gendxAllele)

        typeloaderData = typeloaderOutput[gendxAllele]
        typeloaderHandle.write("Closest Allele : %s\n\n" % typeloaderData["closestAllele"])

        for feature, coordinates in zip(typeloaderData["features"],typeloaderData["coordinates"]):
            if feature == "utr5":
                typeloaderHandle.write("UTR5\t\t")
            elif feature == "utr3":
                typeloaderHandle.write("UTR3\t\t")
            else:
                featureNum, featureCode = feature
                if featureCode == "e":
                    featureName = "Exon"
                    typeloaderHandle.write("%s %s\t\t" % (featureName, featureNum))
                else:
                    featureName = "Intron"
                    typeloaderHandle.write("%s %s\t" % (featureName, featureNum))
            typeloaderHandle.write("%s\t%s\n" % (coordinates[0], coordinates[1]))

        typeloaderHandle.write("\nDifferences to Closest Known Allele\n")
        if typeloaderData["isExactMatch"]: typeloaderHandle.write("None\n")
        else:
            diffData = typeloaderData["differences"]

            if len(diffData["mismatchPositions"]):
                mismatches, mismatchPositions = diffData["mismatches"], diffData["mismatchPositions"]
                typeloaderHandle.write("Mismatches : ")
                for mmIndex in range(len(mismatches)):
                    ##print mismatches, mismatchPositions
                    mmLocationData, mmBases = mismatchPositions[mmIndex], mismatches[mmIndex]
                    mmPos, codon = mmLocationData
                    if not codon:
                        typeloaderHandle.write("%s:%s->%s(Intronic)\t" % (mmPos,mmBases[1],mmBases[0]))
                    else:
                        typeloaderHandle.write("%s:%s->%s(Codon %s)\t" % (mmPos,mmBases[1],mmBases[0], codon))
                typeloaderHandle.write("\n")

            if len(diffData["deletionPositions"]):
                typeloaderHandle.write("Deletions : ")
                for deletion in diffData["deletionPositions"]:
                    deletionPos, codon = deletion
                    if not codon:
                        typeloaderHandle.write("%s(Intronic)\t" % deletionPos)
                    else:
                        typeloaderHandle.write("%s(Codon %s)\t" % (deletionPos, codon))
                typeloaderHandle.write("\n")

            if len(diffData["insertionPositions"]):
                typeloaderHandle.write("Insertions : ")
                for insertion in diffData["insertionPositions"]:
                    insertionPos, codon = insertion
                    if not codon:
                        typeloaderHandle.write("%s(Intronic)\t" % insertionPos)
                    else:
                        typeloaderHandle.write("%s(Codon %s)\t" % (insertionPos, codon))
                typeloaderHandle.write("\n")

        typeloaderHandle.write("\n" * 3)
    typeloaderHandle.close()
    """
