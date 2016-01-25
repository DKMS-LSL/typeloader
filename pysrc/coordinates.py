# This routine establishes the co-ordinates for the new allele from the closest known allele
# The closest known allele is determined using getclosestKnownAllele from closestallele.py

# hard coding these locations for now, this should change later
# ideally a routine to download the dat file and parse it automatically
allelesFilename = "/home/vineeth/genemodel_aligner/hla.dat"
geneFamily = "HLA"

from hla_embl_parser import read_dat_file
from closestallele import getClosestKnownAlleles
from imgtTransform import changeToImgtCoords
from Bio import SeqIO

from copy import copy
from sys import argv
from pickle import load
from math import ceil


def getMismatchData(annotations):
    
    
    cdsMap = annotations["cdsMap"]
    alleleSeq = annotations["sequence"]
    
    
    genomicExonCoords = cdsMap.keys()
    genomicExonCoords.sort()
    
    cdsSeq = "".join([alleleSeq[start:end] for (start,end) in genomicExonCoords])
    closestAlleleCdsSeq = annotations["closestAlleleCdsSeq"]
    
    mmCodons = []
    
    exon1Length = genomicExonCoords[0][1]
    numExon1Coords = int(ceil(float(exon1Length)/3))
    
    for mmIndex in len(annotations["differences"]["mismatches"]):
        genomicPos, cdsPos = annotations["differences"]["mismatchPositions"][mmIndex], \
                             annotations["imgtDifferences"]["mismatchPositions"][mmIndex]
        if genomicPos == cdsPos:
            mmCodons.append(())
            continue
        
        canonicalMMCodonNum = int(ceil(float(cdsPos))/3)
        
        # IMGT assigns the first codon in exon 2 as codon 1, and the codons in exon 1 with a -1 backwards 
        if canonicalMMCodonNum > numExon1Coords: imgtMMCodonNum = canonicalMMCodonNum - numExon1Coords
        else: imgtMMCodonNum = canonicalMMCodonNum - (numExon1Coords + 1)
        
        
        if not (cdsPos % 3):# coords stored are 1-based, python indices are 0-based
            actualCodonSeq, closestCodonSeq = cdsSeq[cdsPos - 3 : cdsPos], closestAlleleCdsSeq[cdsPos - 3 : cdsPos]
        elif (cdsPos % 3) == 2:
            actualCodonSeq, closestCodonSeq = cdsSeq[cdsPos - 2 : cdsPos + 1], closestAlleleCdsSeq[cdsPos - 2 : cdsPos + 1]
        else:
            actualCodonSeq, closestCodonSeq = cdsSeq[cdsPos - 1 : cdsPos + 2], closestAlleleCdsSeq[cdsPos - 1 : cdsPos + 2]
            
        mmCodons.append((imgtMMCodonNum,(actualCodonSeq, closestCodonSeq)))
            
    return mmCodons
            

def getCoordinates(blastXmlFilename, allelesFilename = allelesFilename, targetFamily = geneFamily):
    
    allAlleles = read_dat_file(allelesFilename, targetFamily)
    closestAlleles = getClosestKnownAlleles(blastXmlFilename)
    annotations = processAlleles(closestAlleles, allAlleles)
    
    seqsFile = blastXmlFilename.replace(".blast.xml",".fa")
    seqsHandle = open(seqsFile)
    seqsHash = SeqIO.to_dict(SeqIO.parse(seqsHandle, "fasta"))
    
    for gendxAllele in annotations.keys():
        alleleSeq = str(seqsHash[gendxAllele].seq)
        annotations[gendxAllele]["sequence"] = alleleSeq
    seqsHandle.close()
    
    return annotations    
    
def processAlleles(closestAlleles, allAlleles):
    
    annotations = {}
    for alleleQuery in closestAlleles.keys():
        if not closestAlleles[alleleQuery]:
            annotations[alleleQuery] = None
            continue
        closestAlleleName, differences, isExactMatch = closestAlleles[alleleQuery]["name"], closestAlleles[alleleQuery]["differences"], \
                                                       closestAlleles[alleleQuery]["exactMatch"]
        
        features, coordinates, closestAlleleCdsSequence = calculateCoordinates(closestAlleleName, allAlleles, differences)
        utr5Length = len(allAlleles[closestAlleleName].UTR5)
        
        features, coordinates, imgtDifferences, cdsMap = changeToImgtCoords(features, coordinates, differences, utr5Length)
        
        
        annotations[alleleQuery] = {"features":features, "coordinates":coordinates, "imgtDifferences": imgtDifferences, "differences":differences, \
                                    "closestAllele":closestAlleleName, "cdsMap":cdsMap, "closestAlleleCdsSequence": closestAlleleCdsSequence, \
                                    "isExactMatch":isExactMatch}
    
    return annotations
        
def getClosestAlleleCoordinates(alleleData):
    
    features = []
    coordinates = []
    closestAlleleCdsSequence = ""
    
    if alleleData.utrpos_dic.has_key("utr5"):
        features.append("utr5")
        coordinates.append((alleleData.utrpos_dic["utr5"][0] + 1, alleleData.utrpos_dic["utr5"][1]))
        
    
    exonIds = [(exonNumber,"e") for exonNumber in alleleData.exonpos_dic.keys()]
    intronIds = [(intronNumber, "i") for intronNumber in alleleData.intronpos_dic.keys()]
    cdsIds = copy(exonIds)
    cdsIds.extend(intronIds)
    
    cdsIds.sort()
    
    features.extend(cdsIds)
    for cdsId in cdsIds:
        if cdsId[1] == "e":
            coordinates.append((alleleData.exonpos_dic[cdsId[0]][0] + 1, alleleData.exonpos_dic[cdsId[0]][1]))
            closestAlleleCdsSequence += alleleData.seq[alleleData.exonpos_dic[cdsId[0]][0] + 1:alleleData.exonpos_dic[cdsId[0]][1] + 1]
        else: coordinates.append((alleleData.intronpos_dic[cdsId[0]][0] + 1, alleleData.intronpos_dic[cdsId[0]][1]))
           
            
    if alleleData.utrpos_dic.has_key("utr3"):
        features.append("utr3")
        coordinates.append((alleleData.utrpos_dic["utr3"][0] + 1, alleleData.utrpos_dic["utr3"][1]))
        
    #coordinates[0] = (coordinates[0][0] + 1, coordinates[0][1])
        
    return (features, coordinates, closestAlleleCdsSequence)
    
def calculateCoordinates(alleleName, alleles, differences = {}):
    
    allele = alleles[alleleName]
    features, coordinates, closestAlleleCdsSequence = getClosestAlleleCoordinates(allele)
    
    
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
        coordinates[coordIndex] = (coordinates[coordIndex][0], coordinates[coordIndex][1]+coordChange)
        
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
            coordinates[nextFeatureIndex] = (coordinates[nextFeatureIndex][0] + coordChange, coordinates[nextFeatureIndex][1] + coordChange)
    
    return (features, coordinates, closestAlleleCdsSequence)

if __name__ == '__main__':
    
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
    
        

    
    

    
    






