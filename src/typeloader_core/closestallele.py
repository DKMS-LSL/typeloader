# This is the TypeLoader BLAST parser for finding the closest known allele for an input sequence

"""
This routine makes the following assumptions :
    1. The sequence being queried is a full length allele
    2. The closest known allele will align as a single HSP ( http://www.ncbi.nlm.nih.gov/BLAST/tutorial/#head2 )
    3. The GenDX generated file will have 2 sequences, only 1 of them is assumed to be not present in the database
"""

from Bio.Blast import NCBIXML
from Bio import SeqIO
from sys import argv
import os

from . import EMBLfunctions as EF
import ntpath

###################################################

def getClosestKnownAlleles(blastXmlFilename, targetFamily, settings, log):

    xmlHandle = open(blastXmlFilename)
    xmlParser = NCBIXML.parse(xmlHandle)

    # get the associated fasta_file
    query_fasta_file = blastXmlFilename.replace("blast.xml", "fa")

    closestAllelesData = parseBlast(xmlParser, targetFamily, query_fasta_file, settings, log)
    
    xmlHandle.close()

    return closestAllelesData

def parseBlast(xmlRecords, targetFamily, query_fasta_file, settings, log):

    """
    Basic description of the XML below
    For more details on parsing the BLAST XML output - http://biopython.org/DIST/docs/tutorial/Tutorial.html#sec:parsing-blast

    Heirarchy of XML output -

    Record (corresponding to each query) -> Alignment (individual hits) -> HSP

    """

    closestAlleles = {}
    for xmlRecord in xmlRecords:

        queryId = xmlRecord.query_id
        output_db = xmlRecord.database
        if output_db.endswith("parsedKIR.fa"):
            output_db = os.path.join(settings["dat_path"], settings["general_dir"], settings["reference_dir"], "parsedKIR.fa")
        elif output_db.endswith("parsedhla.fa"):
            output_db = os.path.join(settings["dat_path"], settings["general_dir"], settings["reference_dir"], "parsedhla.fa")
        else:
            log.error("Unknown reference file (in closestallele.py):", output_db)
        alignments = xmlRecord.alignments
        queryLength = xmlRecord.query_length

        potentialClosestAlleleAlignment = alignments[0]
        hsps = potentialClosestAlleleAlignment.hsps

        closestAlleleName = potentialClosestAlleleAlignment.hit_def
        if closestAlleleName.find(targetFamily) == -1:
            if closestAlleleName.startswith("MIC") and targetFamily == "HLA":
                pass
            else:
                closestAlleleName = potentialClosestAlleleAlignment.hit_id

        ref_sequence = SeqIO.to_dict(SeqIO.parse(output_db, "fasta"))[closestAlleleName].seq
        query_sequence = SeqIO.to_dict(SeqIO.parse(query_fasta_file, "fasta"))[queryId].seq
        hsp_query, hsp_subject, hsp_match, concatHSPS, hsp_start = puzzleHspsFromFirstHit(hsps, ref_sequence, query_sequence, query_fasta_file)

        if hsp_query == "" and hsp_subject == "" and hsp_match == "":
            closestAlleles[queryId] = None
        else:
            closestAlleles[queryId] = closestAlleleItems(hsp_query, hsp_subject, hsp_match, closestAlleleName, concatHSPS, hsp_start)

    if hsp_start != 1:
        log.warning("Incomplete sequence found: first {} bp missing!".format(hsp_start - 1))
    return closestAlleles

def closestAlleleItems(hsp_query, hsp_subject, hsp_match, closestAlleleName, concatHSPS, hsp_start):

    # "-" in the query means a deletion, "-" in the hit means an insertion, a gap in the alignment is a mismatch
    deletionPositions = [pos + 1 for pos in range(len(hsp_query)) if hsp_query[pos] == "-"]
    insertionPositions = [pos + 1 for pos in range(len(hsp_subject)) if hsp_subject[pos] == "-"]
    mismatchPositions = [pos + 1 for pos in range(len(hsp_match)) if ((hsp_match[pos] == " ") \
                                                                              and ((pos+1) not in deletionPositions) and ((pos+1) not in insertionPositions))]
    # bases
    deletions = [hsp_subject[deletionPos - 1] for deletionPos in deletionPositions]
    insertions = [hsp_query[insertionPos - 1] for insertionPos in insertionPositions]

    if not(len(deletionPositions) or len(insertionPositions) or len(mismatchPositions)): exactMatch = True
    else: exactMatch = False

    mismatches = list(zip([hsp_query[mismatchPos - 1] for mismatchPos in mismatchPositions], \
                         [hsp_subject[mismatchPos - 1] for mismatchPos in mismatchPositions]))

    differences = {'deletionPositions':deletionPositions, 'insertionPositions':insertionPositions, 'mismatchPositions':mismatchPositions, \
                       'mismatches':mismatches, 'deletions':deletions, 'insertions':insertions}

    closestAllele = {"name":closestAlleleName,"differences":differences, 
                    "exactMatch":exactMatch, "concatHSPS":concatHSPS,
                    "hitStart":hsp_start}

    return closestAllele

def puzzleHspsFromFirstHit(hsps, ref_sequence, query_sequence, query_fasta_file):

    # TODO: (future) Validation of HSP puzzle, until that, take first HSP
    
    potentialClosestHSP = hsps[0]
    hsp_query = potentialClosestHSP.query
    hsp_subject = potentialClosestHSP.sbjct
    hsp_match = potentialClosestHSP.match
    hsp_start = potentialClosestHSP.sbjct_start
    concatHSPS = False

    """

    1. Iterate through each hsp in the first hit
    2. possible cuts (X):

        a:              |========|
                             XXXX
                            |============|
            result:              |=======|

        b:                      |========|
                                 XXXX
                        |============|
            result:     |=======|

        c:              |============|          |============|
                                 XXXX            XXXX
                                |====================|
            result:                  |==========|

    3. every other possibility will be ignored

    """

    """

    hspMap = {}
    bool_sequence = [0] * len(ref_sequence)

    for hsp in hsps:

        overlap_beginning_start = 0
        overlap_beginning_end = 0
        overlap_beginning_end_marker = -1
        overlap_zeros_before = False
        overlap_break = 0
        hsp_break = False

        for run in range(hsp.sbjct_start - 1, hsp.sbjct_end):
            overlap_break += 1
            if bool_sequence[run] == 1:
                # it's an overlap

                # case a:
                if hsp.sbjct_start - 1 + overlap_beginning_start == run: overlap_beginning_start += 1

                # case b:
                if hsp.sbjct_start - 1 + overlap_break - 1 == run and overlap_zeros_before:
                    if overlap_beginning_end_marker == -1: overlap_beginning_end_marker = overlap_break - 1
                    if overlap_beginning_end_marker + overlap_beginning_end != run: break
                    overlap_beginning_end += 1
            else:
                # no overlap
                if overlap_beginning_start > 0 and overlap_beginning_end > 0:
                    # case c:
                    hsp_break = True
                    break
                bool_sequence[run] = 1
                overlap_zeros_before = True

        # break if:
        #   1: if query is a completely overlap
        #   2: query is not one of the cutting cases
        if overlap_beginning_start == hsp.sbjct_end - hsp.sbjct_start + 1 or hsp_break: break

        # next: add query to hspMap:
        save_sbjct_start = hsp.sbjct_start + overlap_beginning_start
        save_sbjct_end = hsp.sbjct_start + overlap_break - overlap_beginning_end - 1
        save_sbjct = hsp.sbjct[overlap_beginning_start:overlap_break - overlap_beginning_end]

        save_query_start = hsp.query_start + overlap_beginning_start
        save_query_end = hsp.query_start + overlap_break - overlap_beginning_end - 1
        save_query = hsp.query[overlap_beginning_start:overlap_break - overlap_beginning_end]

        save_mismatch = hsp.match[overlap_beginning_start:overlap_break - overlap_beginning_end]

        print "save_sbjct_start ", save_sbjct_start, "real_start ", hsp.sbjct_start
        print "save_sbjct_end ", save_sbjct_end, "real_end ", hsp.sbjct_end
        print "save_query_start", save_query_start, "real_start ", hsp.query_start
        print "save_query_end ", save_query_end, "real_end ", hsp.query_end
        print "overlap_beginning_start " , overlap_beginning_start
        print "overlap_beginning_end " , overlap_beginning_end
        print "overlap_break " , overlap_break
        print "hsp_break ", hsp_break
        #print "\n\n"

        hspMap[save_sbjct_start] = [save_sbjct_start, save_sbjct_end, save_sbjct, save_query_start, save_query_end, save_query, save_mismatch]

    hsp_query = ""
    hsp_subject = ""
    hsp_match = ""
    iter_step = 1

    concatHSPS = True if len(hspMap) > 1 else False
    if concatHSPS: EF.write_log(err_file, "WARNING", "Used more than 1 HSP in BLAST algorithm by using " + query_fasta_file)

    # return empty string, if subject not start at position 1
    # otherwise: wrong positions!
    if bool_sequence[0] == 0:
        return (hsp_query, hsp_subject, hsp_match, concatHSPS)
    """

    """
    hspMap_Keys:
        0 = subject start
        1 = subject end
        2 = subject nucleotides
        3 = query start
        4 = query end
        5 = query nucleotides
        6 = mismatch signs
    """

    """
    for key in sorted(hspMap.iterkeys()):

        if iter_step == 1:

            # first iteration
            hsp_subject = hspMap[key][2]
            hsp_query = hspMap[key][5]
            hsp_match = hspMap[key][6]

        else:

            #print "last: " , "subS: ", hspMap[last_key][0], "subE: " ,hspMap[last_key][1], "querS: ", hspMap[last_key][3], "querE: ", hspMap[last_key][4]
            #print "now: " , "subS: ", hspMap[key][0], "subE: ", hspMap[key][1], "querS: ", hspMap[key][3], "querE: ", hspMap[key][4]

            if hspMap[last_key][4] >= hspMap[key][3]:

                #print "overlap deletion"
                hsp_starting_point = 1
                diff = hspMap[last_key][4]-hspMap[key][3]
                deleted_nucleotides = ref_sequence[hspMap[last_key][1]-diff:hspMap[key][0]]
                inserted_nucleotides = ""

            elif hspMap[last_key][1] >= hspMap[key][0]:

                #print "overlap insertion"
                hsp_starting_point = 1
                diff = hspMap[last_key][1] - hspMap[key][0]
                inserted_nucleotides = query_sequence[hspMap[last_key][4]:hspMap[key][3]]
                deleted_nucleotides = ""

            else:

                #print "no overlapping"
                hsp_starting_point = 0
                diff = 0
                deleted_nucleotides = ref_sequence[hspMap[last_key][1]:hspMap[key][0] - 1]
                inserted_nucleotides = query_sequence[hspMap[last_key][4]:hspMap[key][3] - 1]

            #print diff
            #print hsp_query
            hsp_subject = hsp_subject[0:len(hsp_subject)-diff]
            hsp_query = hsp_query[0:len(hsp_query)-diff]
            hsp_match = hsp_match[0:len(hsp_match)-diff]
            #print hsp_query

            new_subject = hspMap[key][2][hsp_starting_point:len(hspMap[key][2])]
            new_query = hspMap[key][5][hsp_starting_point:len(hspMap[key][5])]
            new_match = hspMap[key][6][hsp_starting_point:len(hspMap[key][6])]

            number_deletions = len(deleted_nucleotides)
            number_insertions = len(inserted_nucleotides)

            #print "number_deletions: ", number_deletions
            #print "deleted: ", deleted_nucleotides
            #print "number_insertions: ", number_insertions
            #print "insertions: ", inserted_nucleotides

            # deletion --> see query
            #hsp_query = hsp_query + "\n" + inserted_nucleotides + "\n" + "".join(["-"]*number_deletions) + "\n" + new_query
            # insertions --> see subject
            #hsp_subject = hsp_subject + "\n" + "".join(["-"]*number_insertions) + "\n" + deleted_nucleotides + "\n" + new_subject
            # mismatches --> see match
            #hsp_match = hsp_match + "\n" + "".join(["X"]*number_insertions) + "\n" + "".join(["X"]*number_deletions) + "\n" + new_match

            # deletion --> see query
            hsp_query = hsp_query + inserted_nucleotides + "".join(["-"]*number_deletions) + new_query
            # insertions --> see subject
            hsp_subject = hsp_subject + "".join(["-"]*number_insertions) + deleted_nucleotides + new_subject
            # mismatches --> see match
            hsp_match = hsp_match + "".join(["X"]*number_insertions) + "".join(["X"]*number_deletions) + new_match

        iter_step += 1
        last_key = key
    """

    """
    curr_file = str.split(ntpath.basename(query_fasta_file), ".")[0]
    filename = "/home/markus/playground/report/Validation_ClosestAllele/output/" + curr_file + ".query.txt"
    filebuff = open(filename,'w')
    filebuff.write(str(hsp_query))
    filebuff.close()

    filename = "/home/markus/playground/report/Validation_ClosestAllele/output/" + curr_file + ".sbjct.txt"
    filebuff = open(filename,'w')
    filebuff.write(str(hsp_subject))
    filebuff.close()

    filename = "/home/markus/playground/report/Validation_ClosestAllele/output/" + curr_file + ".mismatch.txt"
    filebuff = open(filename,'w')
    filebuff.write(str(hsp_match))
    filebuff.close()
    """

    return (hsp_query, hsp_subject, hsp_match, concatHSPS, hsp_start)

if __name__ == "__main__":
    pass