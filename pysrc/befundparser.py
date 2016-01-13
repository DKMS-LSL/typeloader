#!/usr/bin/env python

useGenesList = ["A1","A2","B1","B2","C1","C2","D1","D2","DQ1","DQ2","DP1","DP2","DR1","DR2"]
changeNamesFor = ["DQ","DP","DR"]
patientIdPos = 0

def getOtherAlleles(befundFile):
    
    befundHandle = open(befundFile)
    header = befundHandle.readline().strip()
    
    parts = header.split(",")
    usePos = []
    genes = []
    for pos in range(len(parts)):
        if parts[pos] in useGenesList:
            genes.append(parts[pos])
            usePos.append(pos)
   
    befund = {}
    for line in befundHandle:
        if not (len(line.strip())): continue
        parts = line.strip().split(",")
        patient = parts[patientIdPos]
        befund[patient] = {}
        
        for pos in usePos:
            befundGeneName = genes[usePos.index(pos)]
            changeName = reduce(lambda x,y: x or y, [befundGeneName.startswith(nameToChange) for nameToChange in changeNamesFor])
            if changeName: geneName = befundGeneName[:2] + "B1"
            else: geneName = befundGeneName[:-1]
            if not len(parts[pos]): continue
            if befund[patient].has_key(geneName): befund[patient][geneName].append(parts[pos])
            else: befund[patient][geneName] = [parts[pos]]
    
    befundHandle.close()
    
    return befund