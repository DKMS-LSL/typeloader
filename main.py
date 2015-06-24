from xmlfuncs import *
from make_ena import *
from make_imgt import *
from sys import argv

xmlData = parseXML(argv[1])
    
alleleName = getAlleleName(xmlData)
haplotypes = getHaplotypeIds(xmlData, alleleName)
sequence = sequenceFromHaplotype(xmlData, haplotypes)
    
posHash = getCoords(xmlData)
enaPosHash = transform(posHash)
    
generalData = make_globaldata(gene="HLA-C",allele="HLA-C*12:new",product="MHC Class-I Antigen", species="Homo sapiens", seqLen=str(len(sequence)))
    
print make_header(header, generalData, enaPosHash) + make_genemodel(exonString, intronString, generalData, enaPosHash) + make_footer(footer, sequence)

cdslength, mmpos = map_mm(posHash, int(argv[2]))
print cdslength, mmpos
print map_to_codon(cdslength, mmpos)


