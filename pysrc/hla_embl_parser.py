# -*- coding: cp1252 -*-
'''
Created on 11.09.2015

parser functions for repeat use

@author: schoene
'''
#===========================================================
#import modules:

from sys import argv
from pickle import dump

#===========================================================
#classes:

class Allele:
    def __init__(self, ID, locus, name, seq, length, UTR5, UTR3, exon_dic, intron_dic, exonpos_dic, intronpos_dic, utrpos_dic, target):
        self.ID = ID # Accession number or name
        self.locus = locus # gene
        self.name = name # allele name
        self.seq = seq.upper() # full sequence in upper case
        self.length = len(seq) # length of sequence
        self.UTR3 = UTR3 # sequence of UTR3
        self.UTR5 = UTR5 # sequence of UTR5
        self.exon_dic = exon_dic # dict of format {1:'EXON1_SEQ', 2:'EXON2_SEQ'...}
        self.intron_dic = intron_dic # dict of format {1:'INTRON1_SEQ', 2:'INTRON2_SEQ'...}
        self.exonpos_dic = exonpos_dic
        self.intronpos_dic = intronpos_dic
        self.utrpos_dic = utrpos_dic 
        self.is_ref = False
        self.full_seq = False # True if at least some introns are known, otherwise false
        if len(intron_dic.keys()) > 0:
            self.full_seq = True
        
        if name.startswith("HLA"):
            name = name.split("-")[1]
#         self.fasta_header = ">%s:%s_%s %s bp" % (target, ID, name, self.length)
        self.fasta_header = ">%s %s bp" % (name, self.length)
        
        # calculate CDS:
        exons = exon_dic.keys()
        exons.sort()
        self.CDS = ""
        for exon in exons:
            self.CDS += exon_dic[exon]
        
    def __repr__(self):
        return self.name

#===========================================================
# reading functions:

def read_dat_file(dat_file, target, verbose = False):
    """reads content of a .dat file (EMBL format),
    returns list of allele objects.
    The parameter 'target' expects one of the following: "HLA", "Blutgruppen","CCR5", "KIR".
    """
    alleles = []
    if verbose:
        print "Lese %s ein..." % dat_file
    with open(dat_file, "r") as f:
        data = f.readlines()
        for i in range(len(data)):
            line = data[i]
            if line.startswith("ID"):
                s = line.split()
                allele_ID = s[1].replace(";","")
                length = s[5]
                seq = ""
                UTR3 = ""
                UTR5 = ""
                UTR5_start = False
                UTR5_end = False
                UTR3_start = False
                UTR3_end = False
                exon_dic = {}
                exonpos_dic = {}
                intron_dic = {}
                intronpos_dic = {}
                utrpos_dic = {} 
                
                if target in ["Blutgruppen","CCR5"]:
                    allele = allele_ID
                    if allele.find("*")>0:
                        locus = allele.split("*")[0]
                    elif allele.find("_")>0:
                        locus = allele.split("_")[0]
                    else:
                        print "!!!Cannot see Locus of Allele %s! Please adjust Input file!" % allele
                        print line
                        sys.exit()
            
            elif line.startswith("DE"):
                s = line.split()
                if target in ["HLA", "HLA_23_with_introns", "Phasing_HLA_23", "KIR"]:
                    allele = s[1][:-1]
                    locus = allele.split("*")[0]

            elif line.startswith("FT"):
                s = line.split()
                if s[1] == "UTR":
                    start = int(s[-1].split(".")[0]) - 1
                    end = int(s[-1].split(".")[-1])

                    if start == 0:
                        UTR5_start = start
                        UTR5_end = end
                        utrpos_dic["utr5"] = (start, end)
                    else:
                        UTR3_start = start
                        UTR3_end = end
                        utrpos_dic["utr3"] = (start, end)
                elif s[1] == "exon":
                    start = int(s[-1].split(".")[0]) - 1
                    end = int(s[-1].split(".")[-1])
                    next_line = data[i+1]
                    assert next_line.find("number") > 0, "Cannot find exon number in %s:\n '%s'\n '%s'" % (allele, line, next_line)
                    exon_num = int(next_line.split('"')[-2])
                    exonpos_dic[exon_num] = (start, end)

                elif s[1] == "intron":
                    start = int(s[-1].split(".")[0]) - 1
                    end = int(s[-1].split(".")[-1])
                    next_line = data[i+1]
                    assert next_line.find("number") > 0, "Cannot find intron number in %s:\n '%s'\n '%s'" % (allele, line, next_line)
                    intron_num = int(next_line.split('"')[-2])
                    intronpos_dic[intron_num] = (start, end)

            elif line.startswith("SQ"):
                read_on = True
                j = 0
                while read_on:
                    j += 1
                    s = data[i+j]
                    if s.startswith("//"):
                        read_on = False
                    else:
                        myseq = "".join(s.split()[:-1]).upper()
                        seq += myseq

            elif line.startswith("//"):
                for exon in exonpos_dic:
                    (start,end) = exonpos_dic[exon]
                    exon_seq = seq[start:end]
                    exon_dic[exon] = exon_seq

                for intron in intronpos_dic:
                    (start,end) = intronpos_dic[intron]
                    intron_seq = seq[start:end]
                    intron_dic[intron] = intron_seq

                if UTR5_end:
                    UTR5 = seq[UTR5_start:UTR5_end].upper()
                if UTR3_end:
                    UTR3 = seq[UTR3_start:UTR3_end].upper()

                myAllele = Allele(allele_ID, locus, allele, seq, length, UTR5, UTR3, exon_dic, intron_dic, exonpos_dic, intronpos_dic, utrpos_dic, target)
                if target == "HLA": # HLA.dat contains other loci, too - MIC, TAP...
                    usable = False
                    usable_loci = ["HLA-A*", "HLA-B*", "HLA-C*", "HLA-DPB1*", "HLA-DQB1*", "HLA-DRB"]
                    for loc in usable_loci:
                        if allele.startswith(loc): # HLA.dat contains other loci, too - MIC, TAP...
                            usable = True
                    if usable:
                        alleles.append(myAllele)
                else:
                    alleles.append(myAllele)
    if verbose:
        print "\t%s Allele von %s erfolgreich eingelesen!" % (len(alleles), target)

    alleleHash = {}
    for allele in alleles:
	alleleHash[allele.name] = allele
    

    return alleleHash


#===========================================================
# writing functions:

def write_fasta(alleles, output_fasta, no_UTR = False, verbose = False):
    """takes a list of allele objects,
    writes a fasta-file containing their full sequences
    """
    if verbose:
        print "Schreibe %s Allele nach %s..." % (len(alleles), output_fasta)
    with open(output_fasta, "w") as g:
        for allele in alleles:
            if no_UTR: # only use sequence without UTR (not always fully known)
#                 print len(allele.UTR5), allele.UTR5
#                 print len(allele.UTR3), allele.UTR3
#                 print len(allele.seq), allele.seq
                start_utr3 = len(allele.UTR3) * -1
                if start_utr3 == 0:
                    allele.print_seq = allele.seq[len(allele.UTR5):]
                else:
                    allele.print_seq = allele.seq[len(allele.UTR5): -1 * len(allele.UTR3)]
#                 print len(allele.print_seq), allele.print_seq
#                 print stop
#                 if allele.name == "HLA-A*74:01":
#                     print len(allele.seq), len(allele.UTR5), len(allele.UTR3)
#                     print allele.seq
#                     print allele.print_seq
#                     stop
            else:
                allele.print_seq = allele.seq
            g.write("%s\n%s\n" % (allele.fasta_header, allele.print_seq))
    if verbose:
        print "\tFertig!"

if __name__ == '__main__':

   imgt_download_file, target = argv[1], argv[2]
   alleles = read_dat_file(imgt_download_file, target)

   alleleDumpFile = open(argv[3], "w")
   dump(alleles, alleleDumpFile)
   alleleDumpFile.close()  
