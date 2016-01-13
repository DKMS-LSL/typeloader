# functions to parse the submission email from ENA to get IDs needed for IMGT submission

# Lines to recognise:

"""
>
> Accession#:  LN912787
> Status:      not confidential
> Description: Homo sapiens HLA-C gene for MHC class I antigen, cell line DKMS-LSL
>             C-520, allele HLA-C*15:new
>
"""

import re
from sys import argv

idsTextBlockRegex = re.compile("(Accession#:(.*?)\n(.*?)Status:(.*?)\n(.*?)Description:(((.*?)\n){1,2}))",re.MULTILINE)

def getAccession(idsTextBlockSearchObject): return idsTextBlockSearchObject.expand("\\2").strip()

def getCellLine(idsTextBlockSearchObject):
    
    cellLineBlock = idsTextBlockSearchObject.expand("\\6")
    cellLineBlockCleaned = re.sub(r"(\s+)","",cellLineBlock.split(",")[1])
    
    cellLineRegex = re.compile("(DKMS(.*?)LSL(.*?)([A-Z]+)(.*?)([0-9]+))")
    cellLineSearchObject = cellLineRegex.search(cellLineBlockCleaned)
    cellLineLetterPart = cellLineSearchObject.expand("\\4")
    cellLineNumberPart = cellLineSearchObject.expand("\\6")
    
    return "DKMS-LSL-%s-%s" % (cellLineLetterPart, cellLineNumberPart)

def getIDs(emailText):
    
    cellLineToAcc = {}
    
    startSearchPos = 0
    textBlockMatch  = idsTextBlockRegex.search(emailText,startSearchPos)
    
    while textBlockMatch:
        
        
        accNum = getAccession(textBlockMatch)
        cellLine = getCellLine(textBlockMatch)
        cellLineToAcc[cellLine] = accNum
        
        startSearchPos = textBlockMatch.end(1)
        textBlockMatch = idsTextBlockRegex.search(emailText,startSearchPos)
        
    return cellLineToAcc

if __name__ == "__main__":
    
    idHash = getIDs(open(argv[1]).read())
    for cellLine in idHash.keys():
        print cellLine, idHash[cellLine]
    



