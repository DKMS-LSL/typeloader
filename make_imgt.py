from bx.intervals import Interval, IntervalTree

def map_to_codon(cdslength,pos):
    
    # given a position in the cds find which codon the pos is in
    
    codonTree = IntervalTree()
    codonNum = 1
    for num in range(1,cdslength+1,3):
        codonTree.add_interval(Interval(num,num+3,value={"codonNum":codonNum})) # taking the codon as 4 bases, bx-python interval finding for terminal ends needs a (pos, pos+1)
        
        codonNum += 1
    
    
    mm_codon = codonTree.find(pos,pos+1) 
    
    return mm_codon[0].value["codonNum"] - 24 # IMGT starts counting the codons with -24 (to maintain backwards compatibility ?)

def map_mm(posHash, mm_pos):
    
    # mm_pos is a gene-based co-ordinate
    # imgt requires this to be CDS based
    
    exonTree = IntervalTree()
    exons = posHash["exons"]

    cdsTransform = {}
    
    cdsExonStart = 0
    for exonindex in range(len(exons)):
        
        begin, end = exons[exonindex][0],exons[exonindex][1]
        
        exonTree.add_interval(Interval(begin, end, value={"exonnum":exonindex+1}))
        cdsTransform[exonindex+1] = ((begin,end),(cdsExonStart+1,cdsExonStart+1+(end-begin)))
        cdsExonStart = cdsExonStart+1+(end-begin)
    cdsLength = cdsExonStart # the end of the last exon is also the length of the cds  (in a 1-based system) in cds space 
    
    exon_with_mm = exonTree.find(mm_pos,mm_pos)
    exonnum = exon_with_mm[0].value["exonnum"]
    
    print cdsTransform
    mm_exon_gene_begin = cdsTransform[exonnum][0][0]
    mm_exon_cds_begin = cdsTransform[exonnum][1][0]
    
    mm_cds_pos = mm_exon_cds_begin + (mm_pos - mm_exon_gene_begin) + 1
    
    return (cdsLength, mm_cds_pos)
        
    
    

