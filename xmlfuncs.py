import xmltodict
from helpers import change_utf_decl
from sys import argv

def parseXML(xmlFileName):
    
    change_utf_decl(xmlFileName) #utf-16 to utf-8 change
    
    xmlHandle = open(xmlFileName)
    xmlText = xmlHandle.read()
    xmlHandle.close()
    
    return xmltodict.parse(xmlText)

def getAlleleName(parsedXML):
    
    # look in xml for matches with minExonMismatches > 0
    
    alleles = parsedXML["sample"]["matchsets"]["matchset"]["matchcombination"]["matchId"] # ask Viviane if there can be more than 1 matchset
    
    for allele in alleles:
        
        exonMismatches = int(allele["@minExonMismatches"])
        if exonMismatches: return allele["#text"]


def getHaplotypeIds(parsedXML, alleleName):
    
    matches = parsedXML["sample"]["matches"]["match"]
    
    for match in matches:
        
        currAlleleName = match["@id"]
        if currAlleleName == alleleName:
            return [haplotype for haplotype in match["haplotypecombination"]["haplotypeId"]]

def sequenceFromHaplotype(parsedXML, haplotypeList):
    
    haplotypes = parsedXML["sample"]["haplotypes"]["haplotype"]
    
    haplotypeSeqs = []
    
    for haplotype in haplotypes:
        if haplotype["@id"] in haplotypeList:
            begin = int(haplotype["@begin"].split(":")[0]) # splitting on the : accounting for phase?descriptor in the XML
            end = int(haplotype["@end"].split(":")[0])
            sequence = haplotype["#text"].replace("-","")
            haplotypeSeqs.append((begin,end,sequence))

    haplotypeSeqs.sort()
    
    return "".join([usedHaplotype[-1] for usedHaplotype in haplotypeSeqs])

def getCoords(parsedXML):
    
    regions = parsedXML["sample"]["reference"]["regions"]["region"]
    
    utr = []
    exonHash, exons = {},[]
    intronHash, introns = {},[]
    
    for region in regions:
        begin,end = int(region["@begin"].split(":")[0]), int(region["@end"].split(":")[0]) # splitting on the : accounting for phase?descriptor in the XML
        
        if region["@id"].find("UTR") != -1:
            utr.append((begin,end))
        else:
            region_num = int(region["@id"].strip().split(" ")[-1])
            if region["@id"].find("Exon") != -1: exonHash[region_num] = (begin,end)
            else: intronHash[region_num] = (begin, end)
    
    utr.sort()
    exon_nums = exonHash.keys()
    exon_nums.sort()
    intron_nums = intronHash.keys()
    intron_nums.sort()
    
    exons = [exonHash[exon_num] for exon_num in exon_nums]
    introns = [intronHash[intron_num] for intron_num in intron_nums]
    
    return {"utr": utr, "exons": exons, "introns": introns}
  
if __name__ == '__main__':
    
    xmlData = parseXML(argv[1])
    
    alleleName = getAlleleName(xmlData)
    print alleleName

    haplotypes = getHaplotypeIds(xmlData, alleleName)
    print haplotypes
    
    sequence = sequenceFromHaplotype(xmlData, haplotypes)
    print sequence
    
    print getCoords(xmlData)
    
    

