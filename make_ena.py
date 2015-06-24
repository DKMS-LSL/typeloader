from xmlfuncs import *
from enaformat import *
from copy import copy

def make_globaldata(species="Homo sapiens", gene="", allele="", partial="", product="",seqLen=""):
   
    globaldata = {"{species}":species,"{gene}":gene,"{allele}":allele,"{partial}":partial,"{product}":product,"{sequence length}":seqLen}
    return globaldata

def transform(posHash):
    
    utr, exons, introns = posHash["utr"], posHash["exons"], posHash["introns"]
    newPosHash = {}
    
    if len(utr):
        if utr[0][0] < -1:
            offset = abs(utr[0][0])
            
            if len(utr) > 1: newPosHash["utr"] = [(1,utr[0][1]+offset),(utr[1][0]+offset,utr[1][1]+offset)]
            else: newPosHash["utr"] = [(1,utr[0][1]+offset),()]
            
            newPosHash["exons"] = [(1,exons[0][1]+offset)]
            newPosHash["exons"].extend([(exon[0]+offset,exon[1]+offset) for exon in exons[1:-1]])
            
            if len(newPosHash["utr"][1]): newPosHash["exons"].append((exons[-1][0]+offset,newPosHash["utr"][1][1]+offset))
            else: newPosHash["exons"].append((exons[-1][0]+offset,exons[-1][1]+offset))
            
            newPosHash["introns"] = [(intron[0]+offset,intron[1]+offset) for intron in introns]
            
        else:
            # no 5' UTR found but 3' UTR exists
            newPosHash["exons"] = [exon for exon in exons[:-1]]
            newPosHash["exons"].append((exons[-1][0],utr[-1][1]))
            newPosHash["introns"] = copy(introns)
            newPosHash["utr"] = [(),utr[-1]]

    else:
        
        newPosHash = copy(posHash)

    newPosHash["cds"] = [(exon[0]+offset,exon[1]+offset) for exon in exons]

    return newPosHash


def make_header(hText, general, enaPosHash):
    
    general["{exon_coord_list}"] = ",".join(["%s..%s" % (region[0],region[1]) for region in enaPosHash["cds"]])
    
    headerop = hText
    for field in general.keys():
        headerop = headerop.replace(field, general[field])
    
    return headerop
    
def make_genemodel(eText,iText,general,enaPosHash, fromExon = 0, toExon = 0):
    
    genemodelop = ""
    
    exons = enaPosHash["exons"]
    introns = enaPosHash["introns"]
    
    for exon_num in range(len(exons)):
        
        if fromExon and ((exon_num + 1) < fromExon): continue
        if toExon and ((exon_num + 1) > toExon): break
        
        exon = exons[exon_num]
        
        genemodelop += eText.replace("{start}",str(exon[0])).replace("{stop}",str(exon[1])).replace("{exon_num}",str(exon_num + 1))
        
        if toExon and ((exon_num + 1) == toExon): break
        
        if (exon_num < (len(exons) - 1)):
            intron = introns[exon_num]
            genemodelop += iText.replace("{start}",str(intron[0])).replace("{stop}",str(intron[1])).replace("{intron_num}",str(exon_num + 1))
            
        genemodelop = genemodelop.replace("{gene}",general["{gene}"]).replace("{allele}",general["{allele}"])
        
    return genemodelop

def make_footer(fText, sequence):
    
    return fText.replace("{sequence}",sequence)

if __name__ == '__main__':
    
    xmlData = parseXML(argv[1])
    
    alleleName = getAlleleName(xmlData)
    haplotypes = getHaplotypeIds(xmlData, alleleName)
    sequence = sequenceFromHaplotype(xmlData, haplotypes)
    
    posHash = getCoords(xmlData)
    enaPosHash = transform(posHash)
    
    generalData = make_globaldata(gene="HLA-C",allele="HLA-C*12:new",product="MHC Class-I Antigen", species="Homo sapiens", seqLen=str(len(sequence)))
    
    print make_header(header, generalData, enaPosHash) + make_genemodel(exonString, intronString, generalData, enaPosHash, 2, 4) + make_footer(footer, sequence)
    
    
    




