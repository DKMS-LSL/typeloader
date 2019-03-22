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
            return (newPosition, codonIndex)

    return (position, None)

def changeToImgtCoords(features, coordinates, differences, utr5Length = 0):

    imgtDifferences = {}

    imgtCoordinates = []
    for key in ["deletionPositions", "insertionPositions", "mismatchPositions"]:
        imgtDifferences[key] = []

    utr5Index = features.index("utr5")
    utr5Start, utr5End = coordinates[utr5Index][0], coordinates[utr5Index][1]
    utr5Length = utr5End - utr5Start + 1
        
    for featureIndex in range(len(features)):
        feature = features[featureIndex]
        if feature == "utr5":
            ft_start = coordinates[featureIndex][0] - (utr5Length + 1)
            ft_end = coordinates[featureIndex][1] - (utr5Length + 1)
        else:
            ft_start = coordinates[featureIndex][0] - utr5Length
            ft_end = coordinates[featureIndex][1] - utr5Length
        
        imgtCoordinates.append((ft_start, ft_end))

    for key in ["deletionPositions", "insertionPositions", "mismatchPositions"]:
        for pos in differences[key]:
            if (pos >= utr5Start) and (pos <= utr5End):
                imgt_pos = pos - utr5Length + 1 # removed 1 => no effect on tests???
            else:
                imgt_pos = pos - utr5Length # removed 1 => no effect on tests???
            imgtDifferences[key].append(imgt_pos)

    for key in ["mismatches", "insertions", "deletions"]:
        imgtDifferences[key] = differences[key]

    cdsMap = constructCDS(features, coordinates)

    for key in ["deletionPositions", "insertionPositions", "mismatchPositions"]:
        for pos in imgtDifferences[key]:
            imgtDifferences[key] = [transformPos(pos, cdsMap) for pos in differences[key]]
    
    return (imgtCoordinates, imgtDifferences, cdsMap)
