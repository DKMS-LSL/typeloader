# This is the TypeLoader BLAST parser for finding the closest known allele for an input sequence

"""
This routine makes the following assumptions :
    1. The sequence being queried is a full length allele
    2. The closest known allele will align as a single HSP ( http://www.ncbi.nlm.nih.gov/BLAST/tutorial/#head2 )
    3. The GenDX generated file will have 2 sequences, only 1 of them is assumed to be not present in the database
"""

from Bio.Blast import NCBIXML
from sys import argv

def getClosestKnownAlleles(blastXmlFilename):
    
    xmlHandle = open(blastXmlFilename)
    xmlParser = NCBIXML.parse(xmlHandle)
    
    closestAllelesData = parseBlast(xmlParser)
    
    xmlHandle.close()
    
    return closestAllelesData 

def parseBlast(xmlRecords):
    
    """
    Basic description of the XML below
    For more details on parsing the BLAST XML output - http://biopython.org/DIST/docs/tutorial/Tutorial.html#sec:parsing-blast
    
    Heirarchy of XML output -
    
    Record (corresponding to each query) -> Alignment (individual hits) -> HSP 
    
    """
    
    closestAlleles = {}
    for xmlRecord in xmlRecords:
        
        queryId = xmlRecord.query_id
        alignments = xmlRecord.alignments
        queryLength = xmlRecord.query_length
        
        potentialClosestAlleleAlignment = alignments[0]
        hsps = potentialClosestAlleleAlignment.hsps
        #if len(hsps) > 1:
        #    closestAlleles[queryId] = None
        #    continue
        
        potentialClosestAlleleLength = potentialClosestAlleleAlignment.length
        potentialClosestHSP = hsps[0]
        
        # "-" in the query means a deletion, "-" in the hit means an insertion, a gap in the alignment is a mismatch
        deletionPositions = [pos for pos in range(len(potentialClosestHSP.query)) if potentialClosestHSP.query[pos] == "-"]
        insertionPositions = [pos for pos in range(len(potentialClosestHSP.sbjct)) if potentialClosestHSP.sbjct[pos] == "-"]
        mismatchPositions = [pos for pos in range(len(potentialClosestHSP.match)) if ((potentialClosestHSP.match[pos] == " ") \
                                                                                  and (pos not in deletionPositions) and (pos not in insertionPositions))]
        
        deletions = [potentialClosestHSP.sbjct[deletionPos] for deletionPos in deletionPositions]
        insertions = [potentialClosestHSP.query[insertionPos] for insertionPos in insertionPositions]
        
        if not(len(deletionPositions) or len(insertionPositions) or len(mismatchPositions)): exactMatch = True
        else: exactMatch = False
        
        closestAlleleName = potentialClosestAlleleAlignment.title.split(" ")[0]
        mismatches = zip([potentialClosestHSP.query[mismatchPos] for mismatchPos in mismatchPositions], \
                         [potentialClosestHSP.sbjct[mismatchPos] for mismatchPos in mismatchPositions])
        
        differences = {'deletionPositions':deletionPositions, 'insertionPositions':insertionPositions, 'mismatchPositions':mismatchPositions, \
                       'mismatches':mismatches, 'deletions':deletions, 'insertions':insertions}
        
        closestAlleles[queryId] = {"name":closestAlleleName,"differences":differences, "exactMatch":exactMatch}
    
    return closestAlleles
        
        
if __name__ == "__main__":
	
	print getClosestKnownAlleles(argv[1])        
        
        
        
        
    
    

