from backend_mismatch import map_mm, map_to_codon
from backend_imgtformat import *
from backend_xmlfuncs import *
from backend_enaformat import *
from copy import copy
import textwrap
from datetime import datetime

def make_imgtglobaldata(submission_id="",allele_counter=1,sequencelength=0,relatedallele="",allelename="",gene=""):
    
    return {"{submission_id}":submission_id,"{allele_counter}":allele_counter,"{sequence length}":sequencelength,"{related allele}":relatedallele,"{allelename}":allelename,"{gene}":gene}


def make_imgtheader(imgtheader,general,coordhash,enaPosHash,mm_pos=0,mm_base="",new_base="",mm_codon="",new_codon=""):
    
    general["{exon_coord_list}"] = ",".join(["%s..%s" % (region[0],region[1]) for region in enaPosHash])
    
    cds_len, cds_mm = map_mm(coordhash, mm_pos)
    mm_codon_num = map_to_codon(cds_len,cds_mm)
    
    general["{mismatch position}"] = cds_mm
    general["{original base}"] = mm_base
    general["{new base}"] = new_base
    general["{original codon}"] = mm_codon
    general["{new codon}"] = new_codon
    general["{mismatch codon}"] = mm_codon_num
    
    todaystr = datetime.now().strftime('%d/%m/%Y')
    general["{submission_date}"] = todaystr
    general["{release_date}"] = todaystr
    
    headerop = imgtheader
    for field in general.keys():
        headerop = headerop.replace(field, str(general[field]))
        
    return headerop
        

def make_imgtgenemodel(imgtexonString,imgtintronString,general,enaPosHash, fromExon = 0, toExon = 0):
    
    genemodelop = ""
    
    exons = enaPosHash["exons"]
    introns = enaPosHash["introns"]
    
    for exon_num in range(len(exons)):
        
        if fromExon and ((exon_num + 1) < fromExon): continue
        if toExon and ((exon_num + 1) > toExon): break
        
        exon = exons[exon_num]
        
        genemodelop += imgtexonString.replace("{start}",str(exon[0])).replace("{stop}",str(exon[1])).replace("{exon_num}",str(exon_num + 1))
        
        if toExon and ((exon_num + 1) == toExon): break
        
        if (exon_num < (len(exons) - 1)):
            intron = introns[exon_num]
            genemodelop += imgtintronString.replace("{start}",str(intron[0])).replace("{stop}",str(intron[1])).replace("{intron_num}",str(exon_num + 1))
            
    return genemodelop

def make_imgtfooter(imgtfooter, sequence, sequencewidth=60): 

    footerop = imgtfooter.replace("{sequence length}",str(len(sequence)))
    footerop = footerop.replace("{countA}",str(sequence.count("A")))
    footerop = footerop.replace("{countG}",str(sequence.count("G")))
    footerop = footerop.replace("{countT}",str(sequence.count("T")))
    footerop = footerop.replace("{countC}",str(sequence.count("C")))
    
    tempseq = copy(sequence)
    tempseq.replace("A","").replace("G","").replace("T","").replace("C","")
    othercount = len(tempseq)
    
    footerop = footerop.replace("{countOther}", str(othercount))
    
    seqlines = textwrap.wrap(sequence,sequencewidth)
    seqstring = ""
    
    padspace = " " * 5
    
    count = 0
    for seqline in seqlines:
        count += 60
        if len(seqline) < 60:
            sepbases = 5 - (len(seqline) / 10)
            nobases = 60 - len(seqline)
            currseq = " ".join(textwrap.wrap(seqline,10))
            currseqstring = padspace + currseq + (" " * (sepbases + nobases)) + padspace + str(len(sequence))
        else:
            currseq = " ".join(textwrap.wrap(seqline,10))
            currseqstring = padspace + currseq + padspace + str(count) + "\n"
        seqstring += currseqstring

    footerop = footerop.replace("{sequence}", seqstring)
    
    return footerop
    
    
    





        
    
    

