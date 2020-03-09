#!/usr/bin/env python

from .backend_enaformat import *
from copy import copy
import textwrap

def make_globaldata(species="Homo sapiens", gene_tag="", gene="", allele="", partial="", product_DE="", product_FT="",
                    function="", seqLen="",cellline="",codonstart="1", pseudogene = ""):

    globaldata = {"{species}":species, "{gene_tag}":gene_tag, "{gene}":gene,"{allele}":allele,"{partial}":partial,
                  "{product_DE}":product_DE,"{product_FT}":product_FT,"{function}":function,"{sequence length}":seqLen,
                  "{cell line}":cellline,"{reading frame}":codonstart, "{pseudogene}":pseudogene}
    return globaldata

def transform(posHash):

    utr, exons, introns, pseudoexons = posHash["utr"], posHash["exons"], posHash["introns"], posHash["pseudoexons"]
    newPosHash = {"utr":[],"exons":{},"introns":{}, "pseudoexons":{}, "cds":{}}
    offset = 0

    min_exon = min(exons, key=int)
    max_exon =  max(exons, key=int)
    first_exon = exons[min_exon]
    last_exon = exons[max_exon]

    if len(utr):
        if utr[0][0] < -1:
            offset = abs(utr[0][0])

            if len(utr) > 1: newPosHash["utr"] = [(1,utr[0][1]+offset),(utr[1][0]+offset,utr[1][1]+offset)]
            else: newPosHash["utr"] = [(1,utr[0][1]+offset),()]

            for number in exons:
                if number == min_exon:
                    # first exon
                    newPosHash["exons"][number] = (1,exons[number][1]+offset)
                elif number == max_exon:
                    # last exon
                    if len(newPosHash["utr"][1]):
                        newPosHash["exons"][number] = (exons[number][0]+offset, newPosHash["utr"][1][1])
                    else:
                        newPosHash["exons"][number] = (exons[number][0]+offset, exons[number][1]+offset)
                else:
                    # all other exons
                    newPosHash["exons"][number] = (exons[number][0]+offset,exons[number][1]+offset)

            # add offset to all introns
            newPosHash["introns"] = {number : (pos[0] + offset, pos[1] + offset) for (number, pos) in list(introns.items())}
            # add offset to all pseudoexons
            newPosHash["pseudoexons"] = {number : (pos[0] + offset, pos[1] + offset) for (number, pos) in list(pseudoexons.items())}
        else:
            # no 5' UTR found but 3' UTR exists
            newPosHash["exons"] = {number : (pos[0], pos[1]) for (number, pos) in list(exons.items()) if number != max_exon}
            newPosHash["exons"][max_exon] = (exons[max_exon][0],utr[-1][1])
            newPosHash["pseudoexons"] = copy(pseudoexons)
            newPosHash["introns"] = copy(introns)
            newPosHash["utr"] = [(),utr[-1]]
    else:
        newPosHash = copy(posHash)
    
    for number, pos in exons.items():
        newPosHash["cds"][number] = (pos[0]+offset,pos[1]+offset)

    return newPosHash

def is_null_allele(sequence, enaPosHash):
    
    # in cds pseudoexons are excluded yet
    cds = enaPosHash["cds"]
    cds_sequence = ""
      
    for key, value in cds.items():
        cds_sequence += sequence[cds[key][0]-1:cds[key][1]]
    
    # cut the last (stop) codon
    cds_sequence = cds_sequence[:-3]     
    seq_len = len(cds_sequence)
    if seq_len % 3 != 0:
        return True, "Attention! Number of exon bases not divisible by 3  => null allele!"
    stop_codons = ["TGA", "TAG", "TAA"]
    for codon in range(1, seq_len, 3):
        if cds_sequence[codon-1:codon+2] in stop_codons:
            return True, "Attention! Preliminary stop codon found => null allele!"        
      
    return False, "No null allele!"

def make_header(backend_dict, general, enaPosHash, null_allele):
    
    if null_allele:
        headerop = backend_dict["header_null_allele"]
    else:
        headerop = backend_dict["header"]
        
    general["{exon_coord_list}"] = ",".join(["%s..%s" % (region[0],region[1]) for key, region in enaPosHash["cds"].items()])
    for field in list(general.keys()):
        headerop = headerop.replace(field, general[field])
    return headerop

def make_genemodel(backend_dict,general,enaPosHash, extraInformation, features):

    eText = backend_dict["exonString"]
    iText = backend_dict["intronString"]
    peText = backend_dict["pseudoExonString"]
    
    pseudoExonsNums = extraInformation["pseudoexon"]
    exonNums = extraInformation["exon_number"]
    intronNums = extraInformation["intron_number"]
    
    genemodelop = ""

    exons = enaPosHash["exons"]
    introns = enaPosHash["introns"]
    pseudoexons = enaPosHash["pseudoexons"]
    
    for featureIndex in range(len(features)):
        feature = features[featureIndex]
        if feature == "utr5" or feature == "utr3": continue
        number = feature[0]
        if feature[1].startswith("e"):
            # feature is an exon
            exon = pseudoexons[number] if feature[1].startswith("epseudo") else exons[number]
            genemodelop += eText.replace("{start}",str(exon[0])).replace("{stop}",str(exon[1])).replace("{exon_num}",str(exonNums[number]))
            if (pseudoExonsNums[number] == True): genemodelop += peText
        else:
            # feature is an intron
            intron = introns[number]
            genemodelop += iText.replace("{start}",str(intron[0])).replace("{stop}",str(intron[1])).replace("{intron_num}",str(intronNums[number]))
        genemodelop = genemodelop.replace("{gene}",general["{gene}"]).replace("{allele}",general["{allele}"])

    return genemodelop

def make_footer(backend_dict, sequence,seqwidth=80):

    fText = backend_dict["footer"]
    sequence_lines = textwrap.wrap(sequence,seqwidth)

    # This is a workaround for ENA ignoring the last line of the sequence if there are only 2 bases on that line (#53)
    # Once ENA fixes this bug, this if section can be removed
    if len(sequence) % seqwidth == 2: 
        new_sequence_lines = sequence_lines[:-2] 
        new_sequence_lines.append(sequence_lines[-2] + sequence_lines[-1])
        sequence_lines = new_sequence_lines
    return fText.replace("{sequence}","\n".join(sequence_lines))


if __name__ == '__main__':

    seq = "AGTTCACAATGA"
    null_allele, msg = is_null_allele(seq)
    print(null_allele, msg)
    
    #xmlData = parseXML(open(argv[1]).read())

    #alleleName = getAlleleName(xmlData)
    #haplotypes = getHaplotypeIds(xmlData, alleleName)
    #sequence = sequenceFromHaplotype(xmlData, haplotypes)

    #print(alleleName)
    #print(haplotypes)

    #posHash = getCoords(xmlData)
    #enaPosHash = transform(posHash)

    #generalData = make_globaldata(gene="HLA-C",allele="HLA-C*12:new",product="MHC Class-I Antigen", species="Homo sapiens", seqLen=str(len(sequence)))

    #print make_header(header, generalData, enaPosHash) + make_genemodel(exonString, intronString, generalData, enaPosHash, fromExon, toExon) + make_footer(footer, sequence)
