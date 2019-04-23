from functools import reduce
#!/usr/bin/env python

# some of the KIR loci have 3 or maybe 4 alleles
# to be prepared, they are in the list, but probably not in the befund.csv
useGenesList = ["A1","A2","B1","B2","C1","C2" \
                ,"DR1","DR2","DQ1","DQ2","DP1","DP2" \
                ,"KIR2DL1-1","KIR2DL1-2","KIR2DL1-3","KIR2DL1-4" \
                ,"KIR2DL2-1","KIR2DL2-2","KIR2DL2-3","KIR2DL2-4" \
                ,"KIR2DL3-1","KIR2DL3-2","KIR2DL3-3","KIR2DL3-4" \
                ,"KIR2DL4-1","KIR2DL4-2","KIR2DL4-3","KIR2DL4-4" \
                ,"KIR2DL5-1","KIR2DL5-2","KIR2DL5-3","KIR2DL5-4" \
                ,"KIR2DP1-1","KIR2DP1-2","KIR2DP1-3","KIR2DP1-4" \
                ,"KIR2DS1-1","KIR2DS1-2","KIR2DS1-3","KIR2DS1-4" \
                ,"KIR2DS2-1","KIR2DS2-2","KIR2DS2-3","KIR2DS2-4" \
                ,"KIR2DS3-1","KIR2DS3-2","KIR2DS3-3","KIR2DS3-4" \
                ,"KIR2DS4-1","KIR2DS4-2","KIR2DS4-3","KIR2DS4-4" \
                ,"KIR2DS5-1","KIR2DS5-2","KIR2DS5-3","KIR2DS5-4" \
                ,"KIR3DL1-1","KIR3DL1-2","KIR3DL1-3","KIR3DL1-4" \
                ,"KIR3DL2-1","KIR3DL2-2","KIR3DL2-3","KIR3DL2-4" \
                ,"KIR3DL3-1","KIR3DL3-2","KIR3DL3-3","KIR3DL3-4" \
                ,"KIR3DP1-1","KIR3DP1-2","KIR3DP1-3","KIR3DP1-4" \
                ,"KIR3DS1-1","KIR3DS1-2","KIR3DS1-3","KIR3DS1-4" \
                ,"MICA-1","MICA-2","MICB-1","MICB-2"]
changeNamesFor = ["DQ","DP","DR"]
patientIdPos = 0
patientIdPos_alt = 1
customerPos = 2

def getOtherAlleles(befundFile):

    befundHandle = open(befundFile)
    header = befundHandle.readline().strip()
    customer_dic = {}

    if "," in header:
        delimiter=","
    elif ";" in header:
        delimiter=";"
    else:
        msg = "Could not figure out delimiter of pretyping file. Please use ',' or ';'!"
        return None, msg
    
    parts = header.split(delimiter)
    usePos = []
    genes = []
    for pos in range(len(parts)):
        if parts[pos] in useGenesList:
            genes.append(parts[pos])
            usePos.append(pos)

    befund = {}
    for line in befundHandle:
        if not (len(line.strip())): continue
        parts = line.strip().split(delimiter)
        patient = parts[patientIdPos]
        patient2 = parts[patientIdPos_alt] # alternately, use 2nd column as user-ID
        customer = parts[customerPos]
        customer_dic[patient] = customer
        customer_dic[patient2] = customer
        befund[patient] = {}
        befund[patient2] = {}

        for pos in usePos:
            befundGeneName = genes[usePos.index(pos)]
            changeName = reduce(lambda x,y: x or y, [befundGeneName.startswith(nameToChange) for nameToChange in changeNamesFor])
            if changeName: 
                geneName = "HLA-" + befundGeneName[:2] + "B1"
            else:
                if befundGeneName.startswith("KIR"): 
                    geneName = befundGeneName[:-2]
                elif befundGeneName.startswith("MIC"):
                    geneName = befundGeneName[:-2]
                else: 
                    geneName = "HLA-" + befundGeneName[:-1]
            if not len(parts[pos]):
                continue
            if geneName in befund[patient]: 
                befund[patient][geneName].append(parts[pos])
            elif geneName in befund[patient2]: 
                befund[patient2][geneName].append(parts[pos])
            else: 
                befund[patient][geneName] = [parts[pos]]
                befund[patient2][geneName] = [parts[pos]]

    befundHandle.close()

    return befund, customer_dic

if __name__ == '__main__':

    from sys import argv
    print(list(getOtherAlleles(argv[1]).keys()))
