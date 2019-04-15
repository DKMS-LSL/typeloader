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

def transformPos(pos_orig, cdsMap, sum_deletes_before, sum_inserts_before, sum_cds_deletes_before, sum_cds_inserts_before):
    
    pos = pos_orig - sum_deletes_before
    cdsRegions = list(cdsMap.keys())
    cdsRegions.sort()

    for region in cdsRegions:
        if (pos >= region[0]) and (pos <= region[1]):
            newRegion = cdsMap[region]
            newPosition = newRegion[0] + (pos - region[0]) - sum_cds_inserts_before + sum_cds_deletes_before
            codonIndex = newPosition / 3 # codon length = 3
            return (newPosition, codonIndex)

    return (pos_orig - sum_inserts_before, None)

def changeToImgtCoords(features, coordinates, differences, utr5Length = 0):

    cdsMap = constructCDS(features, coordinates)
    
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

    # shift positions for preceding inDels:
    ins_in_cds = []
    del_in_cds = []
    for key in ["deletionPositions", "insertionPositions", "mismatchPositions"]:
        imgtDifferences[key] = []
        new_diff = []
        for pos in differences[key]:
            sum_deletes_before = sum([1 for posx in differences["deletionPositions"] if posx < pos])
            sum_cds_deletes_before = sum([1 for posx in differences["deletionPositions"] if posx < pos and posx in del_in_cds])
            sum_inserts_before = sum([1 for posx in differences["insertionPositions"] if posx < pos])
            sum_cds_inserts_before = sum([1 for posx in differences["insertionPositions"] if posx < pos and posx in ins_in_cds])
            newpos = transformPos(pos, cdsMap, sum_deletes_before, sum_inserts_before, sum_cds_deletes_before, sum_cds_inserts_before)
            imgtDifferences[key].append(newpos)
#             print(key, pos, sum_inserts_before, sum_deletes_before, sum_cds_deletes_before, sum_cds_inserts_before, newpos)
            # adjust differences[key] for preceding insertions:
            if newpos[1]: # if change located in CDS
                new_diff.append(pos)
                if key == "insertionPositions":
                    ins_in_cds.append(pos)
                elif key == "deletionPositions":
                    del_in_cds.append(pos)
            else:
                new_diff.append(newpos[0])
        differences[key] = new_diff
                
    for key in ["mismatches", "insertions", "deletions"]:
        imgtDifferences[key] = differences[key]

    
    return (imgtCoordinates, imgtDifferences, cdsMap)
