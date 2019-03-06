#!/usr/bin/env python

import contextlib
import re, os
from zipfile import ZipFile
from configparser import ConfigParser

from .befundparser import getOtherAlleles
from .coordinates import getCoordinates
from .enaemailparser import parse_embl_response
from .imgt_text_generator import make_imgt_text
from .errors import IncompleteSequenceError, BothAllelesNovelError, InvalidPretypingError
from os import path
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

#     print(cellPatientMap)
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


def get_IPD_counter(config_file, lock_file, settings, log):
    """checks if IPD_counter is currently locked;
    if not, gets current counter;
    if yes, creates lock_file + returns counter + config-parser object (later needed to update the value)
    """
    log.debug("Getting current count of IPD submissions...")
    if os.path.isfile(lock_file):
        msg = "Another user is currently creating IPD files.\n"
        msg += "Please try again in a minute or so, to make sure you don't create files with the same IPD number."
        log.warning(msg)
        return False, msg
    
    if settings["modus"] == "productive":
        with open(lock_file, "w") as _: # create lockfile
            log.debug("Creating IPD counter lockfile under {}...".format(lock_file))
            os.utime(lock_file)
    
    cf = ConfigParser()
    cf.read(config_file)
    num = cf.get("Counter", "ipd_submissions")
    try:
        num = int(num)
    except Exception as E:
        log.error(E)
        log.exception(E)
        msg = "ipd_submissions counter must be an integer. '{}' is not!".format(num)
        os.remove(lock_file)
        return False, msg
        
    log.debug("\tCurrent count = {}".format(num))
    return True, (num, cf)


def format_submission_id(fixedString, variablePartLength, submissionCounter):
    """creates name of IPD file
    """
    fixedString += "1"
    numberStringLength = len(str(submissionCounter))
    numberOfZeroes = int(variablePartLength) - numberStringLength

    submissionId = fixedString + ("0" * numberOfZeroes) + str(submissionCounter)
    return submissionId


def update_IPD_counter(new_value, cf, config_file, lock_file, log):
    """updates the IPD_counter in the config lie and removes the accompanying lockfile,
    so other users can use it again
    """
    log.debug("Setting current count of IPD submissions to {}...".format(new_value))
    cf.set("Counter", "ipd_submissions", str(new_value))
    with open(config_file, "w") as g:
        cf.write(g)
    os.remove(lock_file)
    log.debug("\t=> success")
    return True


def make_imgt_data(project_dir, samples, file_dic, allele_dic, cellEnaIdMap, geneMapENA, befund_csv_file,
                   settings, log):
    log.debug("Making IPD data...")
        
    geneMap = {"gene":[settings["gene_hla"], settings["gene_kir"]]}
    (patientBefundMap, customer_dic) = getPatientBefund(befund_csv_file)
    if not patientBefundMap:
        msg = customer_dic
        log.warning(msg)
        return False, msg, None
    
    imgt_data = {}

    cell_lines = {}
    
    config_file = os.path.join(settings["root_path"], "_general", "counter_config.ini")
    lock_file = os.path.join(settings["root_path"], "_general", "ipd_nr.lock")
    success, result = get_IPD_counter(config_file, lock_file, settings, log)
    if not success:
        msg = result
        log.warning(msg)
        return success, msg, None
    
    (submissionCounter, counter_cf) = result
    fixedString = settings["ipd_shortname"]
    variablePartLength = settings["ipd_submission_length"]
    multi_dic = {} # contains alleles with multiple novel alleles
    problem_dic = {} # contains alleles with invalid pretypings
    
    for (sample, local_name, IPD_ID) in samples:
        enafile = path.join(project_dir, sample, file_dic[local_name]["ena_file"])
        if not path.exists(enafile):
            msg = "Can't find ena file: {}".format(enafile)
            log.warning(msg)
            with contextlib.suppress(FileNotFoundError):
                os.remove(lock_file)
            return False, msg, None
        
        blastOp = path.join(project_dir, sample, file_dic[local_name]["blast_xml"])
        if not path.exists(blastOp): 
            msg = "Can't find blast.xml file: {}".format(blastOp)
            log.warning(msg)
            with contextlib.suppress(FileNotFoundError):
                os.remove(lock_file)
            return False, msg, None
        try: 
            enaId = cellEnaIdMap[local_name]
        except KeyError:
            msg = "Can't find ENA ID for {}".format(local_name)
            log.warning(msg)
            with contextlib.suppress(FileNotFoundError):
                os.remove(lock_file)
            return False, msg, None
        try: 
            gene = geneMapENA[local_name]
        except KeyError:
            msg = "Can't find gene for {}".format(local_name)
            log.warning(msg)
            with contextlib.suppress(FileNotFoundError):
                os.remove(lock_file)
            return False, msg, None

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
            with contextlib.suppress(FileNotFoundError):
                os.remove(lock_file)
            log.warning(msg)
            return False, msg, None

        newAlleleStub = getNewAlleleNameFromEna(enafile).split(":")[0]
        try: 
            annotations = getCoordinates(blastOp, allelesFilename, targetFamily, settings, log, isENA=False)
        except IncompleteSequenceError as E:
            return False, (" {}:\n".format(local_name)) + E.msg, None
        except Exception as E:
            print("Blast output : ", blastOp)
            print(allelesFilename, targetFamily)
            log.error(E)
            log.exception(E)
            log.warning("Blast messed up?")
            with contextlib.suppress(FileNotFoundError):
                os.remove(lock_file)
            msg = "Encountered a BLAST problem!\n"
            msg += "Please restart TypeLoader to update the reference files."
            return False, msg, None
        
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
        
        if IPD_ID:
            submissionId = IPD_ID
        else:
            submissionCounter = submissionCounter + 1
            submissionId = format_submission_id(fixedString, variablePartLength, submissionCounter)
        cell_lines[local_name] = submissionId
        
        if sample in local_name: # allele created with V2.2.0 or higher
            cell_line = "_".join(local_name.split("_")[:-2])
        else:
            cell_line = local_name
        
        try:
            imgt_data[submissionId] = make_imgt_text(submissionId, cell_line, local_name, allele_dic[local_name], 
                                                     enaId, befund,  
                                                     closestAllele, diffToClosest, imgtDiff, 
                                                     enafile, sequence, geneMap, settings, log)
        except BothAllelesNovelError as E:
            multi_dic[local_name] = [sample, local_name, E.allele, E.alleles]
        except InvalidPretypingError as E:
            problem_dic[local_name] = [sample, local_name, E.locus, E.allele_name, E.alleles, E.problem]
    
    if settings["modus"] == "productive":
        update_IPD_counter(submissionCounter, counter_cf, config_file, lock_file, log)
    
    if problem_dic:
        log.debug("\t=> encountered a problem in {} samples: please fix".format(len(problem_dic)))
        return False, "Invalid pretypings", problem_dic
    elif multi_dic:
        log.debug("\t=> encountered multiple novel alleles in {} samples: please fix".format(len(multi_dic)))
        return False, "Multiple novel alleles in target locus", multi_dic
    else:
        log.debug("\t=> successfully made IPD data")
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

def write_imgt_files(project_dir, samples, file_dic, allele_dic, ENA_id_map, ENA_gene_map,
                     befund_csv_file, submission_name, 
                     folderpath, settings, log):
    success = True
    error = None
    customer_dic = None
    resultText = ""
    zip_file = ""
    imgt_files = []
    cell_lines = []
    imgt_file_names = None
    
    try:
        log.debug("\tMaking IPD data...")
        results = make_imgt_data(project_dir, samples, file_dic, allele_dic, ENA_id_map, ENA_gene_map, 
                                 befund_csv_file, settings, log)
        if not results[0]: # encountered problem
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
        return False, repr(E)

    return (zip_file, cell_lines, customer_dic, resultText, imgt_file_names, success, error)


if __name__ == '__main__':

#     ena_email_file, befund_file, cellLine_patient_file, submissionId, imgt_filepath, enaFileLoc = argv[1:]
#     print(write_imgt_files(ena_email_file, befund_file, cellLine_patient_file, submissionId, imgt_filepath, enaFileLoc))
#     
    get_cellLine_patient_map(cellLine_patient_file)