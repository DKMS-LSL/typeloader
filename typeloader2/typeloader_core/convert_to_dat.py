#!/usr/bin/env python3
# -*- coding: cp1252 -*-
"""
Created on 2020-11-12

This script converts TypeLoader-generated IPD and ENA files into .dat files,
which can be visually analyzed in CLC Main Workbench

@author: Bianca Schoene
"""

# import modules:
import textwrap
from itertools import groupby
import os

# ===========================================================
# classes:

class Allele:
    def __init__(self, name, features, CDS_string, seq, src="ENA"):
        self.name = name
        self.features = features
        self.seq = seq.lower().replace(" ", "")
        self.CDS_string = CDS_string
        self.make_seq_header()
        self.make_padded_seq()
        if src == "ENA":
            self.recover_UTRs()

    def recover_UTRs(self):
        """in ENA files, the UTRs are annotated as part of the first ad last exon.
         The positions can be inferred from the CDS-line, though.
         """
        self.CDS = self.CDS_string.split("join(")[1].split(")")[0].split(",")
        ex1 = self.CDS[0].split("..")
        ex1_start = int(ex1[0])
        ex1_end = int(ex1[1])

        ex_last = self.CDS[-1].split("..")
        ex_last_start = int(ex_last[0])
        ex_last_end = int(ex_last[1])

        UTR5_line = ex1_line = UTR3_line = ex_last_line = None
        if ex1_start != 1:  # UTR5 exists:
            UTR5_line = f"FT   UTR             1..{ex1_start - 1}\n"
            ex1_line = f"FT   exon            {ex1_start}..{ex1_end}\n"

        if ex_last_end != self.seq_len:
            UTR3_line = f"FT   UTR             {ex_last_end + 1}..{self.seq_len}\n"
            ex_last_line = f"FT   exon            {ex_last_start}..{ex_last_end}\n"

        fts_new = []

        boundaries_section = False
        boundaries = []

        exon = []
        for line in self.features:
            if line.startswith("FT   exon            1.."):
                boundaries_section = True
            if boundaries_section:
                if line.startswith("FT   exon") or line.startswith("FT   intron"):
                    if exon:
                        boundaries.append(exon)
                    exon = []
                exon.append(line)
            else:
                fts_new.append(line)

        boundaries.append(exon)

        if UTR5_line:
            fts_new.append(UTR5_line)
            ex1 = boundaries[0]
            boundaries = boundaries[1:]
            fts_new.append(ex1_line)
            for line in ex1[1:]:
                fts_new.append(line)

        if UTR3_line:
            last_ex = boundaries[-1]
            boundaries = boundaries[:-1]
            new_ex = [ex_last_line]
            for line in last_ex[1:]:
                new_ex.append(line)

            boundaries.append(new_ex)

        for ex in boundaries:
            for line in ex:
                fts_new.append(line)

        if UTR3_line:
            fts_new.append(UTR3_line)

        self.features = fts_new

    def make_seq_header(self):
        self.seq_len = len(self.seq)
        self.seq_base_dic = {}
        n_count = len(self.seq)
        for char in ("a", "c", "t", "g"):
            count = self.seq.count(char)
            self.seq_base_dic[char] = count
            n_count -= count

        assert n_count >= 0
        self.seq_header = f"SQ   Sequence {self.seq_len} BP; {self.seq_base_dic['a']} A; {self.seq_base_dic['c']} C; " \
                          f"{self.seq_base_dic['g']} G; {self.seq_base_dic['t']} T; {n_count} other;\n"

    def make_padded_seq(self):
        seqlines = textwrap.wrap(self.seq, 60)
        seqstring = ""

        padspace = " " * 5

        count = 0
        for seqline in seqlines:
            count += 60
            if len(seqline) < 60:
                sepbases = 5 - (len(seqline) // 10)
                nobases = 60 - len(seqline)
                currseq = " ".join(textwrap.wrap(seqline, 10))
                currseqstring = padspace + currseq + (" " * (sepbases + nobases)) + padspace + str(len(self.seq))
            else:
                currseq = " ".join(textwrap.wrap(seqline, 10))
                currseqstring = padspace + currseq + padspace + str(count) + "\n"
            seqstring += currseqstring.lower()

        self.seq_padded = seqstring

    def __repr__(self):
        return self.name


# ===========================================================
# functions:

def find_longest_whitespace(line):
    """https://stackoverflow.com/a/12505450/1413513
    """
    current_max = 0
    split_string = line.split(" ")

    for c, sub_group in groupby(split_string):
        if c != '':
            continue

        i = len(list(sub_group))
        if i > current_max:
            current_max = i

    return current_max


def find_appendix(filename):
    """if filename contains suffix '_old' or '_new', remember it to add it to sequence ID
    """
    if "_new." in filename:
        appendix = "_new"
    elif "_old." in filename:
        appendix = "_old"
    else:
        appendix = ""
    return appendix


def read_ENA_file(myfile, appendix, log):
    log.info(f"Reading {myfile} (ENA)...")
    ID = ""
    FTs = []
    seq = ""
    CDS = ""

    with open(myfile, "r") as f:
        seq_started = False
        CDS_started = False
        for line in f:
            if line.startswith("DE"):
                ID = line.split("cell line ")[1].split(",")[0] + appendix
            elif line.startswith("FH") or line.startswith("FT"):
                FTs.append(line)
                if line.startswith("FT   CDS"):
                    CDS_started = True
                    CDS = ""
                if CDS_started:
                    CDS += line.strip()
                    if ")" in line:
                        CDS_started = False
            elif line.startswith("SQ"):
                seq_started = True
            elif line.startswith(r"//"):
                seq_started = False
            else:
                if seq_started:
                    seq += line.strip()
    allele = Allele(ID, FTs, CDS, seq)
    log.info("\t=> done")
    return allele


def read_IPD_file(myfile, appendix, log):
    log.info(f"Reading {myfile} (IPD)...")
    ID = ""
    FTs = []
    seq = ""
    CDS = ""

    with open(myfile, "r") as f:
        seq_started = False
        for line in f:
            n = find_longest_whitespace(line)
            line = line.replace(" " * n, " " * (n + 1))  # adjust padding to correct length
            if line.startswith("ID "):
                ID = line.split()[1].split(";")[0] + appendix
            elif line.startswith("FH") or line.startswith("FT"):
                line = line.replace('"', "").replace("Exon", "exon").replace("Intron", "intron") \
                    .replace("5'UTR", "UTR  ").replace("3'UTR", "UTR  ")
                FTs.append(line)
                if line.startswith("FT   CDS"):
                    CDS = line.strip()
            elif line.startswith("SQ"):
                seq_started = True
            elif line.startswith(r"//"):
                seq_started = False
            else:
                if seq_started:
                    seq += line.strip().split("     ")[0]
    allele = Allele(ID, FTs, CDS, seq, src="IPD")
    log.info("\t=> done")
    return allele


def write_dat(allele, input_file, mydir, log):
    input_stub, _ = os.path.splitext(input_file)
    output_file = os.path.join(mydir, input_stub + ".dat")
    log.info(f"Writing .dat file for allele {allele} to {os.path.basename(output_file)}...")
    with open(output_file, "w") as g:
        g.write(f"ID   {allele.name}; SV 1; standard; DNA; HUM; {len(allele.seq)} BP.\nXX\n")
        for line in allele.features:
            g.write(line)
        g.write(allele.seq_header)
        g.write(allele.seq_padded)
        g.write("\n//")
    log.info(f"\t=> written to {output_file}")


# ===========================================================
# main:

def main(mydir, input_file, filetype, log):
    myfile = os.path.join(mydir, input_file)
    appendix = find_appendix(input_file)
    if filetype.upper() == "ENA":
        allele = read_ENA_file(myfile, appendix, log)
    elif filetype.upper() == "IPD":
        allele = read_IPD_file(myfile, appendix, log)
    write_dat(allele, input_file, mydir, log)


if __name__ == "__main__":
    from .. import general

    MYDIR = r"C:\Users\schoene\WorkFolders\Code\typeloader2\typeloader2\temp"
    INPUT_FILE = "DKMS10010276.txt"
    INPUT_FILE = "DKMS-LSL_ID15519262_E_1.ena.txt"
    FILETYPE = "ENA"  # either ENA or IPD

    log = general.start_log(level="DEBUG")
    log.info("<Start>")
    main(MYDIR, INPUT_FILE, FILETYPE, log)
    log.info("<End>")
