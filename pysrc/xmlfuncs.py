import xmltodict
from helpers import change_utf_decl
from sys import argv

def parseXML(xmlFileName):
    
    change_utf_decl(xmlFileName) #utf-16 to utf-8 change
    
    xmlHandle = open(xmlFileName)
    xmlText = xmlHandle.read()
    xmlHandle.close()
    
    return xmltodict.parse(xmlText)

def getAlleleNames(parsedXML):
    
    # look in xml for matches with minExonMismatches > 0
    
    try: alleles = parsedXML["sample"]["matchsets"]["matchset"]["matchcombination"]["matchId"] # ask Viviane if there can be more than 1 matchset
    except: alleles = parsedXML["Sample"]["Matchsets"]["Matchset"]["Matchcombination"]["MatchId"]
        
    try: return [allele["#text"] for allele in alleles]
    except: return [allele["@refAllele"] for allele in alleles]

def getHaplotypeIds(parsedXML, alleleName):
    
    try: matches = parsedXML["sample"]["matches"]["match"]
    except: matches = parsedXML["Sample"]["Matches"]["Match"]
    
    for match in matches:
        
        currAlleleName = match["@id"]
        if currAlleleName == alleleName:
            try: return [haplotype for haplotype in match["haplotypecombination"]["haplotypeId"]]
            except: return [haplotype for haplotype in match["Haplotypecombination"]["HaplotypeId"]]
                
def sequenceFromHaplotype(parsedXML, haplotypeList):
    
    try: haplotypes = parsedXML["sample"]["haplotypes"]["haplotype"]
    except: haplotypes = parsedXML["Sample"]["Haplotypes"]["Haplotype"]
    
    haplotypeSeqs = []
    
    for haplotype in haplotypes:
        if haplotype["@id"] in haplotypeList:
            begin = int(haplotype["@begin"].split(":")[0]) # splitting on the : accounting for phase?descriptor in the XML
            end = int(haplotype["@end"].split(":")[0])
            sequence = haplotype["#text"].replace("-","")
            haplotypeSeqs.append((begin,end,sequence))

    haplotypeSeqs.sort()
    
    return "".join([usedHaplotype[-1] for usedHaplotype in haplotypeSeqs])

def get_allele_sequences(xmlFile):
    
    xmlData = parseXML(xmlFile)
    
    alleles = {}
    
    alleleNames = getAlleleNames(xmlData)
    for alleleName in alleleNames:
        
        alleles[alleleName] = sequenceFromHaplotype(xmlData, getHaplotypeIds(xmlData, alleleName))
        
    return alleles
  
if __name__ == '__main__':
    
    xmlData = parseXML(argv[1])
    
    alleleName = getAlleleName(xmlData)
    print alleleName

    haplotypes = getHaplotypeIds(xmlData, alleleName)
    print haplotypes
    
    sequence = sequenceFromHaplotype(xmlData, haplotypes)
    print sequence
    
    print getCoords(xmlData)
    
    

