from xmlfuncs import *
from sys import argv
from os import system


"""
The BLAST db has to be formatted like so:
~/blast/ncbi-blast-2.2.31+/bin/makeblastdb -dbtype nucl -in parsedhla.fa -parse_seqids -out parsedhla

The FASTA file corresponding to the GenDX file and the BLAST output file will all be written to the same location
as the GenDX XML file
"""

def getAlleleSequences(xmlFile):
    
    xmlData = parseXML(xmlFile)
    
    alleles = {}
    
    alleleNames = getAlleleNames(xmlData)
    
    for alleleName in alleleNames:
        alleles[alleleName] = sequenceFromHaplotype(xmlData, getHaplotypeIds(xmlData, alleleName))
        
    return alleles

def blastSequences(inputFastaFile, database="/home/vineeth/genemodel_aligner/parsedhla", blastOutputFormat = "5"): # 5 corresponds to XML BLAST output
    
    blastXmlOutputFile = inputFastaFile.replace(".fa",".blast.xml")
    
    discard = system("/home/vineeth/blast/ncbi-blast-2.2.31+/bin/blastn -query %s -parse_deflines -db %s -outfmt %s -out %s" % \
                    (inputFastaFile, database, blastOutputFormat, blastXmlOutputFile))
                
    return blastXmlOutputFile
    

def blastGenDXSeqs(genDXFilename):
    
    alleles =  getAlleleSequences(genDXFilename)
    
    fastaFilename = genDXFilename.replace(".xml",".fa")
    fastaFile = open(fastaFilename, "w")
    for alleleName in alleles.keys():
        fastaFile.write(">%s\n" % alleleName)
        fastaFile.write("%s\n" % alleles[alleleName])
    fastaFile.close()
    
    return blastSequences(fastaFilename)

if __name__ == '__main__':
    
    print blastGenDXSeqs(argv[1])
        

    


