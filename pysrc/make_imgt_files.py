#!/usr/bin/env python

"""

"""

from enaemailparser import getIDs
from befundparser import getOtherAlleles
from coordinates import getCoordinates
from imgt_text_generator import make_imgt_text

import datetime
from sys import argv
import re
from os import path, mkdir, system

blastFileLoc = "/downloads/xmlfiles"

alleleFromEnaRegex = re.compile("(DE(.*?)allele(.*?))")

def parse_email(ena_email_file):
    
    # Parse the ENA email to map the cell line numbers (DKMS-LSL-*-*) to the ENA assigned accession numbers 
    
    ena_email_handle = open(ena_email_file)
    cellLineEna = getIDs(ena_email_handle.read())
    ena_email_handle.close()
    
    return cellLineEna

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
    
    return cellPatientMap

def getPatientBefund(befundFile):
    
    # this file comes exported from the LIMS and lists the alleles that have been typed for a given patient
    
    befund = getOtherAlleles(befundFile)
    return befund


def getNewAlleleNameFromEna(enaFile):
    
    enaHandle = open(enaFile)
    enaText = enaHandle.read()
    enaHandle.close()
    
    newAlleleName = alleleFromEnaRegex.search(enaText).expand("\\3").strip()
    
    return newAlleleName

def format_submission_id(submissionCounter):
    
    fixedString = "DKMS1"
    variablePartLength = 7
    
    numberStringLength = len(str(submissionCounter))
    numberOfZeroes = 7 - numberStringLength
    
    submissionId = fixedString + ("0" * numberOfZeroes) + str(submissionCounter)
    return submissionId

def make_imgt_data(ena_email_file, befund_csv_file, cellLine_patient_file, submissionStart, enaFileLoc):
    
    cellPatientMap = get_cellLine_patient_map(cellLine_patient_file)
    patientBefundMap = getPatientBefund(befund_csv_file)
    cellEnaIdMap = parse_email(ena_email_file)
    
    
    imgt_data = {}

    submissionCounter = int(submissionStart)
    for cellLine in cellPatientMap.keys():
        
        try: patientId = cellPatientMap[cellLine]
        except KeyError: continue
        enafile = path.join(enaFileLoc,cellLine + ".txt")
        if not path.exists(enafile): continue
        blastOp = path.join(blastFileLoc,patientId + ".blast.xml")
        try: enaId = cellEnaIdMap[cellLine]
        except KeyError: continue
        try: befund = patientBefundMap[patientId]
        except KeyError: continue
        
        newAlleleStub = getNewAlleleNameFromEna(enafile).split(":")[0]
        
        annotations = getCoordinates(blastOp)
        for genDxAlleleName in annotations.keys():
            if annotations[genDxAlleleName]["closestAllele"].startswith(newAlleleStub):
                diffToClosest = annotations[genDxAlleleName]["differences"]
                closestAllele = annotations[genDxAlleleName]["closestAllele"]
                sequence = annotations[genDxAlleleName]["sequence"]
                break

        submissionId = format_submission_id(submissionCounter)  
        imgt_data[submissionId] = make_imgt_text(submissionId, cellLine, enaId, befund, closestAllele, diffToClosest, enafile, sequence)
        
        submissionCounter = submissionCounter + 1
    
    return imgt_data

def write_imgt_files(ena_email_file, befund_csv_file, cellLine_patient_file, submissionStart, folderpath, enaFileLoc):
    
    imgt_data = make_imgt_data(ena_email_file, befund_csv_file, cellLine_patient_file, submissionStart, enaFileLoc)
    for submissionId in imgt_data.keys():
        imgt_path = path.join(folderpath, "%s.txt" % submissionId)
        imgt_handle = open(imgt_path,"w")
        imgt_handle.write(imgt_data[submissionId])
        imgt_handle.close()
    
    discard = system("zip -q -r %s %s" % (folderpath,folderpath))
    
    return "%s.zip" % folderpath
    

if __name__ == '__main__':
    
    ena_email_file, befund_file, cellLine_patient_file, submissionId, imgt_filepath, enaFileLoc = argv[1:]
    print write_imgt_files(ena_email_file, befund_file, cellLine_patient_file, submissionId, imgt_filepath, enaFileLoc)
    
    

