# -*- coding: cp1252 -*-
'''
Created on 11.09.2015

parser functions for repeat use

@author: schoene
'''
#===========================================================
#import modules:

import os, re
from pickle import dump
import sys

#===========================================================
#classes:

class Allele:
    def __init__(self, ID, locus, name, seq, length, UTR5, UTR3, exon_dic, intron_dic, exonpos_dic, intronpos_dic, utrpos_dic, pseudo_exon_dic, exon_num_dic, intron_num_dic, target):
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
        self.pseudo_exon_dic = pseudo_exon_dic # dict of format {1:'False', 2:'True', ...}
        self.exon_num_dic = exon_num_dic # dict of formart {1: '1', 3: '3/4', ...}
        self.intron_num_dic = intron_num_dic # dict of formart {1: '1', 2: '2', ...}
        self.is_ref = False
        self.full_seq = False # True if at least some introns are known, otherwise false
        if len(list(intron_dic.keys())) > 0:
            self.full_seq = True
        if name.startswith("HLA"):
            name = name.split("-")[1]
#         self.fasta_header = ">%s:%s_%s %s bp" % (target, ID, name, self.length)
        self.fasta_header = ">%s %s bp" % (name, self.length)

        # calculate CDS:
        exons = list(exon_dic.keys())
        exons.sort()
        self.CDS = ""
        for exon in exons:
            self.CDS += exon_dic[exon]

    def __repr__(self):
        return self.name

#===========================================================
# reading functions:

def read_dat_file(dat_file, target, log, isENA = False, verbose = False):
    """reads content of a .dat file (EMBL format),
    returns list of allele objects.
    The parameter 'target' expects one of the following: "HLA", "Blutgruppen","CCR5", "KIR".
    """
    alleles = []
    version = ""
    curr_release_pattern1 = "\(rel. (.*?), current release"
    curr_release_regex1 = re.compile(curr_release_pattern1) 
    curr_release_pattern2 = "\(rel. (.*?), last updated"
    curr_release_regex2 = re.compile(curr_release_pattern2)

    if verbose:
        log.info("Reading {}...".format(dat_file))
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
                pseudo_exon_dic = {}
                intron_num_dic = {}
                exon_num_dic = {}

                if target in ["Blutgruppen","CCR5"]:
                    allele = allele_ID
                    if allele.find("*")>0:
                        locus = allele.split("*")[0]
                    elif allele.find("_")>0:
                        locus = allele.split("_")[0]
                    else:
                        log.error("!!!Cannot see Locus of Allele %s! Please adjust Input file!" % allele)
                        log.error(line)
                        sys.exit()

            elif line.startswith("DT"):
                line = line.lower()
                for regex in (curr_release_regex1, curr_release_regex2):
                    match = regex.search(line)
                    if match:
                        version = match.groups()[0]
                
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
                    # doublesplit, because of [/number="3/4"] lines
                    exon_num = int(next_line.split('"')[-2].split('/')[0])
                    exonpos_dic[exon_num] = (start, end)
                    exon_num_dic[exon_num] = next_line.split('"')[-2]
                    # look at line + 2, to find pseudoexon
                    next_line = data[i+2]
                    pseudo_exon_dic[exon_num] = True if next_line.find("pseudo") > 0 else False

                elif s[1] == "intron":
                    start = int(s[-1].split(".")[0]) - 1
                    end = int(s[-1].split(".")[-1])
                    next_line = data[i+1]
                    assert next_line.find("number") > 0, "Cannot find intron number in %s:\n '%s'\n '%s'" % (allele, line, next_line)
                    # doublesplit, because of [/number="3/4"] lines
                    intron_num = int(next_line.split('"')[-2].split('/')[0])
                    intronpos_dic[intron_num] = (start, end)
                    intron_num_dic[intron_num] = intron_num = next_line.split('"')[-2]

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

                myAllele = Allele(allele_ID, locus, allele, seq, length, UTR5, UTR3, exon_dic, intron_dic, exonpos_dic, intronpos_dic, utrpos_dic, pseudo_exon_dic, exon_num_dic, intron_num_dic, target)
                if target == "HLA": # HLA.dat contains other loci, too - MIC, TAP...
                    usable = False
                    usable_loci = ["HLA-A*", "HLA-B*", "HLA-C*", "HLA-E*", "HLA-DPB1*", "HLA-DQB1*", "HLA-DRB", "MICA", "MICB", "HLA-DPA1", "HLA-DQA1"]
                    for loc in usable_loci:
                        if allele.startswith(loc): # HLA.dat contains other loci, too - MIC, TAP...
                            usable = True
                    if usable:
                        alleles.append(myAllele)
                else:
                    alleles.append(myAllele)
    if verbose:
        log.info("\t=> successfully read {} of {} alleles!" % (len(alleles), target))

    alleleHash = {}
    for allele in alleles:
        #if not isENA:
        #    if allele.name.find("DQB1") != -1:
        #       if ((allele.name != "HLA-DQB1*05:03:01:01") or (allele.name != "HLA-DQB1*06:01:01")): continue
        alleleHash[allele.name] = allele

    return alleleHash, version


#===========================================================
# writing functions:

def write_fasta(alleles, output_fasta, no_UTR = False, verbose = False):
    """takes a list of allele objects,
    writes a fasta-file containing their full sequences
    """
    if verbose:
        print("Schreibe %s Allele nach %s..." % (len(alleles), output_fasta))
    with open(output_fasta, "w") as g:
        for allele in alleles:
            if no_UTR: # only use sequence without UTR (not always fully known)
                start_utr3 = len(allele.UTR3) * -1
                if start_utr3 == 0:
                    allele.print_seq = allele.seq[len(allele.UTR5):]
                else:
                    allele.print_seq = allele.seq[len(allele.UTR5): -1 * len(allele.UTR3)]
            else:
                allele.print_seq = allele.seq
            g.write("%s\n%s\n" % (allele.fasta_header, allele.print_seq))
    if verbose:
        print("\tFertig!")

def make_parsed_files(target, ref_dir, log):
    """creates the parsed reference files from IPD's files
    """
    ipd_download_file = os.path.join(ref_dir, "{}.dat".format(target))
    fa_filename = os.path.join(ref_dir, "parsed{}.fa".format(target))
    dump_filename = os.path.join(ref_dir, "parsed{}.dump".format(target))
    version_file = os.path.join(ref_dir, "curr_version_{}.txt".format(target.lower()))
    
    log.debug("\t\tReading alleles from {}...".format(ipd_download_file))
    alleles, version = read_dat_file(ipd_download_file, target.upper(), log)
    
    log.debug("\t\tWriting {}...".format(fa_filename))
    with open(fa_filename, "w") as fasta_file:
        for allele_name in list(alleles.keys()):
            allele_data = alleles[allele_name]
            if (target == "hla"):
                if allele_name.startswith("MIC"): # take only full length MIC alleles
                    if ((len(allele_data.UTR3) > 0) & (len(allele_data.UTR5) > 0)):
                        fasta_file.write(">%s\n" % allele_name)
                        fasta_file.write("%s\n" % allele_data.seq)
                else:
                    fasta_file.write(">%s\n" % allele_name)
                    fasta_file.write("%s\n" % allele_data.seq)
            elif (target == "KIR"):
                # take only full length KIR alleles
                if ((len(allele_data.UTR3) > 0) & (len(allele_data.UTR5) > 0)):
                    fasta_file.write(">%s\n" % allele_name)
                    fasta_file.write("%s\n" % allele_data.seq)
            else: 
                pass
    
    log.debug("\t\tWriting {}...".format(dump_filename))
    with open(dump_filename, "wb") as alleleDumpFile:
        dump(alleles, alleleDumpFile)
        
    log.debug("\t\tWriting {}...".format(version_file))
    with open(version_file, "w") as g:
        g.write(version)
    return version

if __name__ == '__main__':
    pass
