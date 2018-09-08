# functions to parse the submission email from ENA to get IDs needed for IMGT submission

# Lines to recognise:

"""
>
> Accession#:  LN912787
> Status:      not confidential
> Description: Homo sapiens HLA-C gene for MHC class I antigen, cell line DKMS-LSL
>             C-520, allele HLA-C*15:new
>

old parsing code:

import re
from sys import argv

idsTextBlockRegex = re.compile("(Accession#:(.*?)\n(.*?)Status:(.*?)\n(.*?)Description:(((.*)\n){1,2}))",re.MULTILINE)

def getAccession(idsTextBlockSearchObject): return idsTextBlockSearchObject.expand("\\2").strip()
def getCellLine(idsTextBlockSearchObject):
    cellLineBlock = idsTextBlockSearchObject.expand("\\6")
    if cellLineBlock.find("null") != -1: return None
    cellLineBlockCleaned = re.sub(r"(\s+)","",[segment for segment in cellLineBlock.split(",") if segment.find("cell line") != -1][0])
    cellLine = cellLineBlockCleaned.split("cellline")[1]
    #cellLineRegex = re.compile("(DKMS(.*?)LSL(.*?)([A-Z]+)([0-9]?)(.*?)([0-9]+))")
    #cellLineSearchObject = cellLineRegex.search(cellLineBlockCleaned)
    #cellLineLetterPart = cellLineSearchObject.expand("\\4")
    #cellLineNumberPart = cellLineSearchObject.expand("\\6")
    if cellLine.find("LSL-") == -1: cellLine = cellLine.replace("LSL","LSL-")
    #return "DKMS-LSL-%s-%s" % (cellLineLetterPart, cellLineNumberPart)
    return cellLine.replace("DKMSLSL","DKMS-LSL")
def getIDs(emailText):
    cellLineToAcc = {}
    startSearchPos = 0
    textBlockMatch  = idsTextBlockRegex.search(emailText,startSearchPos)
    while textBlockMatch:
        accNum = getAccession(textBlockMatch)
        cellLine = getCellLine(textBlockMatch)
	print type(cellLine)
	print type(accNum)
        if cellLine: cellLineToAcc[cellLine] = accNum
        startSearchPos = textBlockMatch.end(1)
        textBlockMatch = idsTextBlockRegex.search(emailText,startSearchPos)
    print type(cellLineToAcc)
    return cellLineToAcc
"""

from sys import argv
from Bio import SeqIO

"""
> new email format: 13.12.2017

ID   LT966078; SV 1; linear; genomic DNA; STD; XXX; 2973 BP.
XX
ST * private
XX
AC   LT966078;
XX
PR   Project:PRJEB23855;
XX
DE   Homo sapiens, HLA-B gene for MHC class I antigen, cell line
DE   DKMS-LSL-B-2273, allele HLA-B*15:new
XX
KW   .
XX
OS   Homo sapiens
OC   unclassified sequences.
XX
RN   [1]
RA   Albrecht V., Albrecht V., Boehme I.;
RT   ;
RL   Submitted (11-DEC-2017) to the INSDC.
RL   DKMS LIFE SCIENCE LAB, Quality & Service, Advanced Projects, Tatzberg 47 ,
RL   Saxony, 01307 Dresden, Germany
XX
FH   Key             Location/Qualifiers
FH
FT   source          1..2973
FT                   /organism="Homo sapiens"
FT                   /mol_type="genomic DNA"
FT                   /cell_line="DKMS-LSL-B-2273"
...

"""

def parse_embl_response(path):

    info_dict = {}
    gene_dict = {}
    gene = ""
    file_handle = open(path,"r")
    for gb_record in SeqIO.parse(file_handle, "embl"):
        for feature in gb_record.features:
            if (feature.type == "source"):
                cell_line = feature.qualifiers.get('cell_line')
                id_acc = gb_record.id.split(".")
                if cell_line: info_dict[cell_line[0].strip()] = id_acc[0]
            if (feature.type == "CDS"):
                # has to be filled once
                # gene = e.g. "HLA-B"
                for qualifier in feature.qualifiers:
                    # either "gene" or "pseudogene" is in the Flatfile
                    # depends on the gene
                    # currently: KIR3DP1 has this tag
                    if (qualifier == 'gene'):
                        gene = feature.qualifiers.get('gene')[0]
                    if (qualifier == 'pseudogene'):
                        gene = feature.qualifiers.get('pseudogene')[0]
            # fill gene for each sample in Flatfile
            # Needed, because different genes could be in one Flatfile
            gene_dict[cell_line[0].strip()] = gene

    #print(info_dict, gene_dict)
    return (info_dict, gene_dict)

if __name__ == "__main__":

    info_dict, gene = parse_embl_response(argv[1])
    print(info_dict)
    #for cellLine in info_dict.keys():
       #print cellLine, info_dict[cellLine]


    #idHash = getIDs(open(argv[1]).read())
    #print idHash
    #for cellLine in idHash.keys():
    #    print cellLine, idHash[cellLine]
