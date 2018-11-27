#!/usr/bin/env python

import datetime
from . import EMBLfunctions as EF
import re, os
from zipfile import ZipFile

from .befundparser import getOtherAlleles
from .coordinates import getCoordinates
from .enaemailparser import parse_embl_response
from .imgt_text_generator import make_imgt_text
from .errors import IncompleteSequenceError
from os import path, mkdir, system
from sys import argv
from functools import reduce

# load .ini file
# hla = EF.ConfigSectionMap('GENES')['hla']
# kir = EF.ConfigSectionMap('GENES')['kir']
# reference_path = EF.ConfigSectionMap('REFERENCE_DATA')['reference_path']
# hla_dat = EF.ConfigSectionMap('REFERENCE_DATA')['hla_dat']
# kir_dat = EF.ConfigSectionMap('REFERENCE_DATA')['kir_dat']
##########################################################

# blastFileLoc = "/downloads/xmlfiles"
# blastFastaFileLoc = "/downloads/fastafiles"
alleleFromEnaRegex = re.compile("(DE(.*?)allele(.*))")
# geneMap = {"gene":[hla, kir]}

def parse_email(ena_email_file):

    # Parse the ENA email to map the cell line numbers (DKMS-LSL-*-*) to the ENA assigned accession numbers
    # 23.01.2018: get targetFamily from ENA response
    cellLineEna, gene = parse_embl_response(ena_email_file)
    return (cellLineEna, gene)

def get_cellLine_patient_map(cellLine_patient_file):

    # This file maps the cell lines to the patient ids
    # sample line in file : DKMS-LSL-C-508	642714.xml
    # we need the patient id to get to the initial BLAST file and for the Befund

    cellLinePatientHandle = open(cellLine_patient_file)
    cellPatientMap = {}
    for line in cellLinePatientHandle:
        parts = line.strip().split("\t")
        cellPatientMap[parts[0]] = parts[1].split(".")[0]
    cellLinePatientHandle.close()

    print(cellPatientMap)
    return cellPatientMap

def getPatientBefund(befundFile):

    # this file comes exported from the LIMS and lists the alleles that have been typed for a given patient
    befund = getOtherAlleles(befundFile)
    return befund

def getNewAlleleNameFromEna(enaFile):

    with open(enaFile) as enaHandle:
        enaText = enaHandle.read()
    
    newAlleleName = alleleFromEnaRegex.search(enaText).expand("\\3").strip()

    return newAlleleName

def format_submission_id(submissionCounter):

    fixedString = "DKMS1"
    variablePartLength = 7

    numberStringLength = len(str(submissionCounter))
    numberOfZeroes = 7 - numberStringLength

    submissionId = fixedString + ("0" * numberOfZeroes) + str(submissionCounter)
    return submissionId

def make_imgt_data(project_dir, samples, file_dic, cellEnaIdMap, geneMapENA, befund_csv_file,
                   submissionStart, settings, log):
    geneMap = {"gene":[settings["gene_hla"], settings["gene_kir"]]}
    (patientBefundMap, customer_dic) = getPatientBefund(befund_csv_file)
    
    if not patientBefundMap:
        msg = customer_dic
        return False, msg
    
    imgt_data = {}

    submissionCounter = int(submissionStart)
    cell_lines = {}
    for (sample, cell_line) in samples:
        enafile = path.join(project_dir, sample, file_dic[cell_line]["ena_file"])
        if not path.exists(enafile):
            msg = "Can't find ena file: {}".format(enafile)
            log.warning(msg)
            return False, msg
        
        blastOp = path.join(project_dir, sample, file_dic[cell_line]["blast_xml"])
        if not path.exists(blastOp): 
            msg = "Can't find blast.xml file: {}".format(blastOp)
            log.warning(msg)
            return False, msg
        try: 
            enaId = cellEnaIdMap[cell_line]
        except KeyError:
            msg = "Can't find ENA ID for {}".format(cell_line)
            log.warning(msg)
            return False, msg
        try: 
            gene = geneMapENA[cell_line]
        except KeyError:
            msg = "Can't find gene for {}".format(cell_line)
            log.warning(msg)
            return False, msg

        # search the current targetfamily and allele DB
        # FF from ENA Email
        if re.search(geneMap["gene"][1], gene):
            targetFamily = geneMap["gene"][1]
            allelesFilename = os.path.join(settings["dat_path"], settings["general_dir"],
                                           settings["reference_dir"], settings["kir_dat"])
        else:
            targetFamily = geneMap["gene"][0]
            allelesFilename = os.path.join(settings["dat_path"], settings["general_dir"],
                                           settings["reference_dir"], settings["hla_dat"])
        geneMap["targetFamily"] = targetFamily
        
        try: 
            befund = patientBefundMap[sample]
        except KeyError:
            msg = "Can't find pretyping for {}.\n(Please make sure that the internal donor ID is listed in the first column of your pretypings file.)".format(sample)
            print(patientBefundMap)
            log.warning(msg)
            return False, msg

        newAlleleStub = getNewAlleleNameFromEna(enafile).split(":")[0]
        try: 
            annotations = getCoordinates(blastOp, allelesFilename, targetFamily, settings, log, isENA=False)
        except IncompleteSequenceError as E:
            return False, (" {}:\n".format(cell_line)) + E.msg
        except Exception as E:
            print("Blast output : ", blastOp)
            print(allelesFilename, targetFamily)
            log.error(E)
            log.exception(E)
            log.warning("Blast messed up?")
            continue
        
        isSameGene = reduce(lambda x,y: x & y, [annotations[genDxAlleleName]["closestAllele"].startswith(newAlleleStub) \
            for genDxAlleleName in list(annotations.keys())])

        for genDxAlleleName in list(annotations.keys()):
            if annotations[genDxAlleleName]["closestAllele"].startswith(newAlleleStub):
                diffToClosest = annotations[genDxAlleleName]["differences"]
                closestAllele = annotations[genDxAlleleName]["closestAllele"]
                sequence = annotations[genDxAlleleName]["sequence"]
                imgtDiff = annotations[genDxAlleleName]["imgtDifferences"]

                if isSameGene:
                    if annotations[genDxAlleleName]["isExactMatch"]: continue
                    else: break
                else:
                    break

        submissionId = format_submission_id(submissionCounter)
        cell_lines[cell_line] = submissionId
        imgt_data[submissionId] = make_imgt_text(submissionId, cell_line, enaId, befund,  
                                                 closestAllele, diffToClosest, imgtDiff, 
                                                 enafile, sequence, geneMap, settings)

        submissionCounter = submissionCounter + 1

    return imgt_data, cell_lines, customer_dic

def zip_imgt_files(folderpath, submission_id, imgt_files, log):
    """zips all generated IPD files in folderpath 
    into zipfile IPD_submission_<submission_id>.zip
    and saves it in folderpath
    """
    log.debug("Zipping files for IMGT...")
    zip_name = "{}.zip".format(submission_id)
    myzip =  os.path.join(folderpath, zip_name)
    with ZipFile(myzip, "w") as z:
        for myfile in imgt_files:
            z.write(myfile, os.path.basename(myfile))
    return myzip

def write_imgt_files(project_dir, samples, file_dic, ENA_id_map, ENA_gene_map,
                     befund_csv_file, submission_name, 
                     folderpath, start_num, settings, log):
    success = True
    error = None
    resultText = ""
    zip_file = ""
    imgt_files = []
    cell_lines = []
    try:
        log.debug("\tMaking IPD data...")
        results = make_imgt_data(project_dir, samples, file_dic, ENA_id_map, ENA_gene_map, 
                                 befund_csv_file, start_num, settings, log)
        if not results[0]:
            return results
        else:
            (imgt_data, cell_lines, customer_dic) = results
        log.debug("\tChecking for ambiguities...")
        resultText = ",".join([imgt_data[submissionId].split(":")[1] for submissionId in list(imgt_data.keys()) \
                               if imgt_data[submissionId].startswith("Ambiguous")])
    
        log.debug("\tWriting IPD files...")
        imgt_file_names = {}
        for submissionId in list(imgt_data.keys()):
            if (re.search("CC   Confirmation", imgt_data[submissionId]) != None):
                imgt_path = path.join(folderpath, "%s_confirmation.txt" % submissionId)
            else:
                imgt_path = path.join(folderpath, "%s.txt" % submissionId)            
            imgt_files.append(imgt_path)
            imgt_file_names[submissionId] = os.path.basename(imgt_path)
            with open(imgt_path, "w") as g:
                g.write(imgt_data[submissionId])
            
        zip_file = zip_imgt_files(folderpath, submission_name, imgt_files, log)
    except Exception as E:
        log.error(E)
        log.exception(E)
        success = False
        error = E

    return (zip_file, cell_lines, customer_dic, resultText, imgt_file_names, success, error)


if __name__ == '__main__':

#     ena_email_file, befund_file, cellLine_patient_file, submissionId, imgt_filepath, enaFileLoc = argv[1:]
#     print(write_imgt_files(ena_email_file, befund_file, cellLine_patient_file, submissionId, imgt_filepath, enaFileLoc))
#     
    get_cellLine_patient_map(cellLine_patient_file)