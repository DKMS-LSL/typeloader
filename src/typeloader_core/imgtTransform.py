def constructCDS(features, coordinates):
    exonCoordinates = [coordinates[featureIndex] for featureIndex in range(len(features)) if features[featureIndex][1] == "e"]
    cdsMap = {}

    cdsStart = 1
    for exonCoord in exonCoordinates:
        exonStart, exonEnd = exonCoord
        cdsEnd = cdsStart + (exonEnd - exonStart)
        cdsMap[(exonStart, exonEnd)] = (cdsStart,cdsEnd)
        cdsStart = cdsEnd + 1

    return cdsMap

def transformPos(position, cdsMap):

    cdsRegions = list(cdsMap.keys())
    cdsRegions.sort()

    for region in cdsRegions:
        if (position >= region[0]) and (position <= region[1]):
            newRegion = cdsMap[region]
            newPosition = newRegion[0] + (position - region[0])
            codonIndex = newPosition / 3 # codon length = 3
            #print position, newPosition
            return (newPosition, codonIndex)

    return (position, None)

def changeToImgtCoords(features, coordinates, differences, utr5Length = 0):

    imgtDifferences = {}

    imgtCoordinates = []
    imgtDifferences["deletionPositions"] = []
    imgtDifferences["insertionPositions"] = []
    imgtDifferences["mismatchPositions"] = []

    if utr5Length:
        utr5Index = features.index("utr5")
        utr5Start, utr5End = coordinates[utr5Index][0], coordinates[utr5Index][1]

        for featureIndex in range(len(features)):
            feature = features[featureIndex]
            if feature == "utr5":
                imgtCoordinates.append((coordinates[featureIndex][0] - (utr5Length + 1), coordinates[featureIndex][1] - (utr5Length + 1)))
            else:
                imgtCoordinates.append((coordinates[featureIndex][0] - utr5Length, coordinates[featureIndex][1] - utr5Length))

        for deletion in differences["deletionPositions"]:
            if (deletion >= utr5Start) and (deletion <= utr5End): imgtDifferences["deletionPositions"].append(deletion - (utr5Length + 1) + 1)
            else: imgtDifferences["deletionPositions"].append(deletion - utr5Length + 1)

        for insertion in differences["insertionPositions"]:
            if (insertion >= utr5Start) and (insertion <= utr5End): imgtDifferences["insertionPositions"].append(insertion - (utr5Length + 1) + 1)
            else: imgtDifferences["insertionPositions"].append(insertion - utr5Length + 1)

        for mismatchPos in differences["mismatchPositions"]:
            if (mismatchPos >= utr5Start) and (mismatchPos <= utr5End): imgtDifferences["mismatchPositions"].append(mismatchPos - (utr5Length + 1) + 1)
            else: imgtDifferences["mismatchPositions"].append(mismatchPos - utr5Length + 1)

        imgtDifferences["mismatches"] = differences["mismatches"]
        imgtDifferences["insertions"] = differences["insertions"]
        imgtDifferences["deletions"] = differences["deletions"]

    else:
        imgtCoordinates = coordinates
        imgtDifferences = differences

    cdsMap = constructCDS(features, coordinates)

    imgtDifferences["deletionPositions"] = [transformPos(deletionPos, cdsMap) for deletionPos in differences["deletionPositions"]]
    imgtDifferences["insertionPositions"] = [transformPos(insertionPos, cdsMap) for insertionPos in differences["insertionPositions"]]
    imgtDifferences["mismatchPositions"] = [transformPos(mismatchPos, cdsMap) for mismatchPos in differences["mismatchPositions"]]

    return (features, imgtCoordinates, imgtDifferences, cdsMap)
