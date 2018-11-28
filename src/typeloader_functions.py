#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on 14.03.2018

typeloader_funtions.py

contains calls to TypeLoader_core and handling thereof


@author: Bianca Schoene
'''

# import modules:
import sys, os, shutil, datetime, re
import string, random
from Bio import SeqIO
from sqlite3 import IntegrityError
from collections import defaultdict

from typeloader_core import (EMBLfunctions as EF, coordinates as COO, backend_make_ena as BME, 
                             backend_enaformat as BE, getAlleleSeqsAndBlast as GASB,
                             closestallele as CA, errors)
import general, db_internal
#===========================================================
# parameters:

from __init__ import __version__
from src.typeloader_core.errors import IncompleteSequenceError

flatfile_dic = {"function_hla" : "antigen presenting molecule",
                "function_kir" : "killer-immunoglobulin receptor",
                "productname_hla_i" : "MHC class I antigen",
                "productname_hla_ii" : "MHC class II antigen",
                "productname_hla_i_null" : "MHC class I antigen null allele",
                "productname_hla_ii_null" : "MHC class II antigen null allele",
                "productname_kir_long" : "Human Killer-cell Immunoglobulin-like Receptor",
                "productname_kir_short" : "Killer-cell Immunoglobulin-like Receptor",
                "species" : "Homo sapiens"}

#===========================================================
# classes:

class Allele():
    def __init__(self, gendx_result, gene, name, product, targetFamily,
                 cellLine = "", newAlleleName = "", partner_allele = ""):
        self.gendx_result = gendx_result
        self.targetFamily = targetFamily
        if targetFamily == "HLA":
            self.gene = "HLA-" + gene
        else:
            self.gene = gene
        self.name = name
        self.product = product
        self.cellLine = cellLine
        self.newAlleleName = newAlleleName
        self.partner_allele = partner_allele
        self.dldfilename = ""
        
#===========================================================
# functions:

def upload_parse_sequence_file(raw_path, settings, log):
    """uploads file from raw_path to temp_dir and parses it
    """
    log.debug("Uploading file {} to temp location...".format(raw_path))
    extension = os.path.splitext(raw_path)[1].lower()
    filetype = None
    
    if extension == ".xml":
        log.debug("XML File found!")
        filetype = "XML"
        
    elif extension in settings["fasta_extensions"].split("|"):
        log.debug("Fasta-File found!")
        filetype = "FASTA"
    else:
        log.error("Input File must be Fasta or XML!")
        return (False, "Unknown file format!", "Input-file should be .xml or .fasta file. Please use a supported file extension!")
    
    # save uploaded file to temp dir:
    try:
        temp_raw_file = os.path.join(settings["temp_dir"], os.path.basename(raw_path))
        log.info("Saving file to {}".format(temp_raw_file))
        shutil.copyfile(raw_path, temp_raw_file)
        log.info("\t=> Done!")
    except Exception as E:
        log.exception(E)
        return False, "Could not save file", "An error occurred during upload of '{}'. Please try again!\n\n{}".format(raw_path, repr(E))
    
    # read file:
    results = GASB.blastRawSeqs(temp_raw_file, filetype, settings, log)
    if results[0] == False: # something went wrong
        return results
    
    (blastXmlFile, targetFamily, fasta_filename, allelesFilename, header_data, xml_data_dic) = results
     
    if header_data:
        sample_name = header_data["LIMS_DONOR_ID"]
    else: 
        sample_name = None
        
    for key in xml_data_dic:
        header_data[key] = xml_data_dic[key]
    
    return True, sample_name, filetype, temp_raw_file, blastXmlFile, targetFamily, fasta_filename, allelesFilename, header_data 

def reformat_header_data(header_data, sample_id_ext, log):
    """translates header data into columns
    """
    log.debug("Translating header...")
    for key in general.header_translation_dic:
        target_key = general.header_translation_dic[key]
        if not header_data[target_key]:
            header_data[target_key] = header_data[key]
    
    # translate DR2S' "ref, second, third" etc. into partner allele:
    partners = []
    for key in ["ref", "second", "third", "fourth"]:
        if key in header_data:
            allele = header_data[key]
            if allele and allele != "NA":
                partners.append(allele)
    header_data["partner_allele"] = " or ".join(partners)
    
    # set default values:
    if header_data["new_software"] == "DR2S":
        if header_data["lr_data"]:
            header_data["lr_phasing"] = "yes" # DR2S always produces phased long read data
    
    # store external sample number if given by parameter (needed for testing):
    if sample_id_ext:
        header_data["Spendernummer"] = sample_id_ext
        
            
def process_sequence_file(project, filetype, blastXmlFile, targetFamily, fasta_filename, allelesFilename, header_data, settings, log):
    log.debug("Processing sequence file...")
    try:
        if filetype == "XML":
            try:
                closestAlleles = CA.getClosestKnownAlleles(blastXmlFile, targetFamily, settings, log)
            except errors.IncompleteSequenceError as E:
                return False, "Incomplete sequence", E.msg
        
            genDxAlleleNames = list(closestAlleles.keys())
            if closestAlleles[genDxAlleleNames[0]] == 0 or closestAlleles[genDxAlleleNames[1]] == 0:
                # No BLAST hit at position 1
                msg = "No BLAST hit at position 1"
                log.warning(msg)
                return False, "Problem in XML file", msg
            
            closestAlleleNames = [closestAlleles[genDxAlleleName]["name"] for genDxAlleleName in genDxAlleleNames]
            geneNames = [alleleName.split("*")[0] for alleleName in genDxAlleleNames]
            alleleNames = ["%s:new" % alleleName.split(":")[0] for alleleName in closestAlleleNames]
             
            products = []
            for geneName in geneNames:
                if geneName.startswith("D"):
                    products.append(flatfile_dic["productname_hla_ii"])
                else:
                    products.append(flatfile_dic["productname_hla_i"])
            
            (gendx_result, gene, name, product) = (genDxAlleleNames[0], geneNames[0], alleleNames[0], products[0])
            allele1 = Allele(gendx_result, gene, name, product, targetFamily)
                 
            (gendx_result, gene, name, product) = (genDxAlleleNames[1], geneNames[1], alleleNames[1], products[1])
            allele2 = Allele(gendx_result, gene, name, product, targetFamily)
            
            myalleles = [allele1, allele2]
            ENA_text = ""
            cellLine = ""
         
        else: # Fasta-File:
            try:
                annotations = COO.getCoordinates(blastXmlFile, allelesFilename, targetFamily, settings, log)
            except errors.IncompleteSequenceError as E:
                return False, "Incomplete sequence", E.msg
            alleles = [allele for allele in annotations.keys()]
            # take the first sequence in fasta file
            alleleName = alleles[0]
            if annotations[alleleName] is None:
                # No BLAST hit at position 1
                msg = "No BLAST hit at position 1"
                log.warning(msg)
                return False, "Problem in XML file", msg
            else:
                extraInformation = annotations[alleleName]["extraInformation"]
                closestAlleleName = annotations[alleleName]["closestAllele"]
                geneName = closestAlleleName.split("*")[0]
                newAlleleName = "%s:new" % closestAlleleName.split(":")[0]
                
                posHash, sequences = EF.get_coordinates_from_annotation(annotations)
            
                currentPosHash = posHash[alleleName]
                sequence = sequences[alleleName]
                features = annotations[alleleName]["features"]
                enaPosHash = BME.transform(currentPosHash)
                null_allele, msg = BME.is_null_allele(sequence, enaPosHash)                
                 
                # set productName and function
                gene_tag = "gene"
                if targetFamily == settings["gene_kir"]: # if KIR
                    productName_FT = geneName + " " + flatfile_dic["productname_kir_short"]
                    productName_DE = flatfile_dic["productname_kir_long"]
                    function = flatfile_dic["function_kir"]
                    if geneName in settings["pseudogenes"].split("|"):
                        gene_tag = "pseudogene"
                else:
                    function = flatfile_dic["function_hla"]
                    geneName = geneName.split("-")[1]
                    # D ...for DQB, DPB, DRB
                    if geneName.startswith("D"):
                        productName_FT = productName_DE = (flatfile_dic["productname_hla_ii"]) \
                            if null_allele == False else (flatfile_dic["productname_hla_ii_null"]) # class 2 gene
                    else:
                        productName_FT = productName_DE = (flatfile_dic["productname_hla_i"]) \
                            if null_allele == False else (flatfile_dic["productname_hla_i_null"]) # class 1 gene
                
                with open(fasta_filename, "rU") as f:
                    parser = SeqIO.parse(f, "fasta")
                    record = parser.__next__()
                    cellLine = record.id.strip()
                 
                generalData = BME.make_globaldata(gene_tag = gene_tag, gene = geneName, allele = newAlleleName, product_DE = productName_DE, product_FT = productName_FT, 
                                                  function = function, species = flatfile_dic["species"], 
                                                  seqLen = str(len(sequence)), cellline = cellLine)
                ENA_text = BME.make_header(BE.backend_dict, generalData, enaPosHash, null_allele) + BME.make_genemodel(BE.backend_dict, generalData, enaPosHash, extraInformation, features, 0, 0) + BME.make_footer(BE.backend_dict, sequence)
                myallele = Allele("", geneName, newAlleleName, productName_FT, targetFamily, cellLine, newAlleleName)
                myalleles = [myallele]
                #TODO (future): accept multiple sequences from one fasta file
        return True, myalleles, ENA_text, cellLine
    except Exception as E:
        log.error(E)
        log.exception(E)
        return False, "Error while processing the sequence file", repr(E)
        


def make_ENA_file(blastXmlFile, targetFamily, allele, settings, log):
    """creates ENA file for allele chosen from XML file
    """
    log.debug("Creating ENA text...")
    allelesFilename = os.path.join(settings["dat_path"],
                                   settings["general_dir"],
                                   settings["reference_dir"],
                                   settings["hla_dat"])
    annotations = COO.getCoordinates(blastXmlFile, allelesFilename, targetFamily, settings, log, isENA=True)
    posHash, sequences = EF.get_coordinates_from_annotation(annotations)
    
    currentPosHash = posHash[allele.alleleName]
    sequence = sequences[allele.alleleName]
    enaPosHash = BME.transform(currentPosHash)
    extraInformation = annotations[allele.alleleName]["extraInformation"]
    features = annotations[allele.alleleName]["features"]
    null_allele, msg = BME.is_null_allele(sequence, enaPosHash)
    
    allele.productName_FT = allele.productName_FT + " null allele" if null_allele else allele.productName_FT

    generalData = BME.make_globaldata(gene_tag = "gene",
                                      gene = allele.geneName, 
                                      allele = allele.newAlleleName, 
                                      product_DE = allele.productName_DE, 
                                      product_FT = allele.productName_FT, 
                                      function = flatfile_dic["function_hla"], 
                                      species = flatfile_dic["species"], 
                                      seqLen = str(len(sequence)), 
                                      cellline = allele.cellLine)
    ENA_text = BME.make_header(BE.backend_dict, generalData, enaPosHash, null_allele) 
    ENA_text += BME.make_genemodel(BE.backend_dict, generalData, enaPosHash, 
                                    extraInformation, features, allele.fromExon, allele.toExon) 
    ENA_text += BME.make_footer(BE.backend_dict, sequence)
    ENA_text = ENA_text.strip()
    
    return ENA_text

def cell_line_looks_ok(cell_line):
    """check cell_line for right pattern,
    if ok return True,
    else popup QMessageBox & return False
    """
    pattern = "^[a-zA-Z0-9_]+-[a-zA-Z0-9_]+-[a-zA-Z0-9-_]+$"
    if re.match(pattern, cell_line):
        return (True, None, None)
    else:
        return (False, "Bad cell_line pattern!", "Cell_lines must follow the pattern <lab>-<locus>-<nr>! All special characters except _ and - are forbidden.")
    
        
def check_cellLine_unique(cell_line, settings, log):
    """checks whether this cell_line already exists in the database;
    if yes, returns False (not unique), if not, returns True
    """
    #TODO: (future) potentially keep all existing cell_lines in a dict => faster?
    query = "select allele_status from alleles where cell_line = '{}'".format(cell_line)
    success, data = db_internal.execute_query(query, 1, log, 
                                              "checking cell-line uniqueness", 
                                              "Database error")
    if not success:
        msg = data
        return (False, "Database error", msg)
        
    if data:
        msg = "Cell line {} already exists! Please change!".format(cell_line)
        return (False, "Cell line not unique!", msg)
    else: # cell line new
        return (True, None, None)


def make_dldfilename(cellLine, filetype):
    """creates download-filename
    """
    raw_filename = cellLine.replace("*","_").replace(":","-") # remove non-allowed characters
    if filetype == "FASTA":
        return raw_filename
    
    s = raw_filename.split("-")
    dldfilename = "-".join(s[:2]) + "-"
    cellLineAlpha = s[2]
    cellLineNum = "-".join(s[3:])
    dldfilename += cellLineAlpha + "-" + cellLineNum
    return dldfilename

       
def move_files_to_sample_dir(project, sample_name, cellLine, filetype,
                             temp_raw_file, blastXmlFile, fasta_filename,
                             settings, log):
    """creates sample_dir and moves all sequence files there,
    renames them to cell line
    """
    dldfilename = make_dldfilename(cellLine, filetype)
    project_dir = os.path.join(settings["projects_dir"], project)
    sample_dir = os.path.join(project_dir, sample_name)
    if not os.path.isdir(sample_dir):
        os.makedirs(sample_dir)
    log.debug("\tMoving files to sample_dir: {}".format(sample_dir))
    raw_file = general.move_rename_file(temp_raw_file, sample_dir, dldfilename)
    blastXmlFile = general.move_rename_file(blastXmlFile, sample_dir, dldfilename)
    if filetype == "XML":
        fasta_filename = general.move_rename_file(fasta_filename, sample_dir, dldfilename)
    else:
        fasta_filename = raw_file
    return sample_dir, raw_file, fasta_filename, blastXmlFile, dldfilename


def save_new_allele(project, sample_name, cell_line, ENA_text,
                    filetype, temp_raw_file, blastXmlFile, fasta_filename,
                    settings, log):
    """saves files of new target allele and writes ENA file
    """
    try:
        # create sample folder & move files there:
        results = move_files_to_sample_dir(project, sample_name, cell_line, 
                                           filetype, temp_raw_file, blastXmlFile, fasta_filename,
                                           settings, log)
        (sample_dir, raw_file, fasta_filename, blastXmlFile, dldfilename) = results
    except Exception as E:
        log.error(E)
        log.exception(E)
        msg = "Could not save the sample's files under {}\n\n{}".format(sample_dir, repr(E))
        return (False, "ENA file creation error", msg, None)
    
    try:
        # write ENA file:
        ena_path = os.path.join(sample_dir, dldfilename + ".ena.txt")
        log.info("\tSaving this allele of sample {} to {}".format(sample_name, ena_path))
        with open(ena_path, "w") as g:
            g.write(ENA_text.strip())
        
    except Exception as E:
        log.error(E)
        log.exception(E)
        msg = "Could not write the ENA file for {}\n\n{}".format(cell_line, repr(E))
        return (False, "ENA file creation error", msg, None)
    
    files = [raw_file, fasta_filename, blastXmlFile, ena_path]
    return (True, None, None, files)


def save_new_allele_to_db(allele, project, sample_name, cell_line,
                          filetype, raw_file, fasta_filename, blastXmlFile,
                          header_data, targetFamily,
                          ena_path, settings, mydb, log):
    """save new allele to internal database
    """
    try:
        log.info("Saving allele {} to database...".format(allele.newAlleleName))
        
        # check if cell line unique:
        query3 = "select count(*) from alleles where cell_line = '{}'".format(cell_line)
        success, data = db_internal.execute_query(query3, 1, log, 
                                                  "checking if cell line already used", 
                                                  err_type = "Database Error", parent = None)
        if success:
            if data != [[0]]:
                msg = "Cell line {} already exists! Please change!".format(cell_line)
                return (False, "Cell line not unique!", msg)
        else:
            return (False, False, False)
        
        # get numbers to increment from database:
        query1 = "select count(*) from alleles where project_name = '{}'".format(project)
        success, data = db_internal.execute_query(query1, 1, log, 
                                                  "retrieving number of alleles for this project from the database", 
                                                  err_type = "Database Error", parent = None)
        if success:
            try:
                project_nr = data[0][0] + 1
            except IndexError:
                project_nr = 1
        else:
            return (False, False, False)
         
        query2 = "select count(*) from alleles where sample_id_int = '{}'".format(sample_name)
        success, data = db_internal.execute_query(query2, 1, log, 
                                                  "retrieving number of alleles for this sample from the database", 
                                                  err_type = "Database Error", parent = None)
        if success:
            try:
                allele_nr = data[0][0] + 1
            except IndexError:
                allele_nr = 1
            if allele_nr > 1:
                log.info("\tThis is allele #{} for this sample!".format(allele_nr))
        else:
            return (False, False, False)
        
        # prepare data:
        if settings["local_name_basis"] == "internal":
            local_name = "_".join([sample_name, allele.gene.replace("HLA-","").replace("KIR",""), str(allele_nr)])
        else:
            local_name = "_".join([header_data["Spendernummer"], allele.gene.replace("HLA-","").replace("KIR",""), str(allele_nr)])
        if targetFamily == "HLA":
            reference = "IPD-IMGT/HLA"
        else:
            reference = "IPD-KIR"
        if not allele.partner_allele:
            allele.partner_allele = header_data["partner_allele"]

        update_queries = []
        # update ALLELES table:
        update_alleles_query = """INSERT INTO alleles 
        (sample_id_int, allele_nr, project_name, project_nr, cell_line, local_name, GENE, 
        Goal, Allele_status, Lab_Status,
        target_allele, partner_allele, reference_database,
        long_read_data, long_read_phasing, long_read_technology,
        short_read_data, short_read_phasing, short_read_technology,
        New_genotyping_software, New_software_version, New_genotyping_date, 
        kommentar, Database_version, upload_date)
        VALUES 
        ('{}', '{}', '{}', {}, '{}', '{}', '{}', 
        'novel', 'ENA-ready', 'completed',
        '{}', '{}', '{}',
        '{}', '{}', '{}',
        '{}', '{}', '{}',
        '{}', '{}', '{}', 
        '{}', '{}', '{}')
        """.format(sample_name, allele_nr, project, project_nr, cell_line, local_name, allele.gene, 
                   allele.newAlleleName, allele.partner_allele, reference,
                   header_data["lr_data"], header_data["lr_phasing"], header_data["lr_tech"], 
                   header_data["sr_data"], header_data["sr_phasing"], header_data["sr_tech"],
                   header_data["new_software"], header_data["new_version"], header_data["new_timestamp"], 
                   header_data["comment"], header_data["ref_version"], general.timestamp('%Y-%m-%d'))
        update_queries.append(update_alleles_query)
        
        # update SAMPLES table:
        query4 = "select count(*) from samples where SAMPLE_ID_INT = '{}'".format(sample_name)
        success, data = db_internal.execute_query(query4, 1, log, 
                                                  "checking if sample already known", 
                                                  err_type = "Database Error", parent = None)
        if success:
            if data != [[0]]:
                pass
            else:
                update_samples_query = """INSERT INTO samples
                (SAMPLE_ID_INT, SAMPLE_ID_EXT) values ('{}', '{}')
                """.format(sample_name, header_data["Spendernummer"])
                update_queries.append(update_samples_query)
        else:
            return (False, False, False)
             
        # update FILES table:
        update_files_query =  """INSERT INTO files
        (Sample_ID_int, cell_line, allele_nr, project, raw_file_type, raw_file, fasta, 
        blast_xml, ena_file) values 
        ('{}', '{}', {}, '{}', '{}', '{}', '{}', 
        '{}', '{}')
        """.format(sample_name, cell_line, allele_nr, project, filetype, os.path.basename(raw_file), os.path.basename(fasta_filename), 
                   os.path.basename(blastXmlFile), os.path.basename(ena_path))
        update_queries.append(update_files_query)
        
        success = db_internal.execute_transaction(update_queries, mydb, log, 
                                                  "saving the novel allele in the database", 
                                                  "Database error")
        if success:
            log.info("\t=> new allele {} successfully saved".format(allele.newAlleleName))
            return (True, None, None)
        else:
            return (False, False, False) 

    except Exception as E:
        log.error(E)
        log.exception(E)
        msg = "An error occurred during the attempt to save this allele to the database. (See below)\nThe allele was not saved!\n\n{}".format(repr(E))
        return (False, "Error during allele saving", msg)


def parse_bulk_csv(csv_file, settings, log):
    """parses a bulk upload csv file,
    returns list of alleles to upload
    """
    import csv
    log.info("Reading .csv file for bulk upload...")
    error_dic = defaultdict(list)
    alleles = []
    allowed_extensions = settings["fasta_extensions"].split("|")
    i = 0
    with open(csv_file, "r") as f:
        data = csv.reader(f, delimiter=",")
        if data:
            for row in data:
                if len(row) > 4:
                    if row[0] != "nr":
                        i += 1
                        err = False
                        nr = row[0]
                        mydir = row[1].strip()
                        myfile = row[2].strip()
                        mypath = os.path.join(mydir, myfile)
                        if not os.path.isfile(mypath):
                            msg = "Could not find file {}".format(mypath)
                            error_dic[nr].append(msg)
                            log.warning("{}: File not found: {}".format(nr, mypath))
                            err = True
                        extension = os.path.splitext(mypath)[-1].lower()
                        if not extension in allowed_extensions:
                            msg = "{} file found! Bulk-upload is only supported for fasta files!".format(extension)
                            error_dic[nr].append(msg)
                            log.warning("{}: {} is not a fasta file".format(nr, myfile))
                            err = True
                        sample_id_int = row[3].strip()
                        sample_id_ext = row[4].strip()
                        customer = row[5].strip()
                        cell_line = row[6].strip()
                        if not err:
                            myallele = [nr, sample_id_int, sample_id_ext, mypath, customer, cell_line]
                            alleles.append(myallele)
    log.info("\t=> {} processable alleles found in {} rows".format(len(alleles), i))
    return alleles, error_dic, i
                        

def bulk_upload_new_alleles(csv_file, project, settings, mydb, log):
    """performs bulk uploading, parsing and saving of new target alleles
    specified in a .csv file 
    """
    log.info("Starting bulk upload from file {}...".format(csv_file))
    alleles, error_dic, num_rows = parse_bulk_csv(csv_file, settings, log)
    successful = []
    for allele in alleles:
        [nr, sample_id_int, sample_id_ext, raw_path, customer, cell_line] = allele
        # check cell-line format:
        (ok, err_type, msg) = cell_line_looks_ok(cell_line)
        if settings["modus"] == "debugging":
            try:
                delete_sample(sample_id_int, 1, project, settings, log)
            except:
                pass
        if not ok:
            error_dic[nr].append(":".join([err_type, msg]))
        else:
            log.info("Uploading #{}: {} ({})...".format(nr, cell_line, sample_id_int))
            # upload raw file:
            results = upload_parse_sequence_file(raw_path, settings, log)
            if results[0] == False: # something went wrong
                error_dic[nr].append(":".join([results[1], results[2]]))
            else:
                log.debug("\t=> success")
                (_, _, filetype, temp_raw_file, blastXmlFile, 
                 targetFamily, fasta_filename, allelesFilename, header_data) = results
                reformat_header_data(header_data, sample_id_ext, log)
                if customer:
                    header_data["Spendernummer"] = customer
                # process raw file:
                sample_name = sample_id_int
                results = process_sequence_file(project, filetype, blastXmlFile, 
                                                targetFamily, fasta_filename, allelesFilename, 
                                                header_data, settings, log)
                if results[0] == False: # something went wrong
                    error_dic[nr].append(":".join([results[1], results[2]]))
                    
                else:
                    log.debug("\t=> success")
                    (_, myalleles, ENA_text, local_cell_line) = results
                    myallele = myalleles[0]
                    if cell_line:
                        ENA_text = ENA_text.replace(local_cell_line, cell_line)
                    
                    # check uniqueness of cell line:
                    (unique, err_type, msg) = check_cellLine_unique(cell_line, settings, log) 
                    if not unique:
                        error_dic[nr].append(":".join([err_type, msg]))
                    else:
                        # save allele files:
                        results = save_new_allele(project, sample_name, cell_line, ENA_text, 
                                                  filetype, temp_raw_file, blastXmlFile, fasta_filename,
                                                  settings, log)
                        (success, err_type, msg, files) = results
                        if not success:
                            error_dic[nr].append(":".join([err_type, msg]))
                        else:
                            [raw_file, fasta_filename, blastXmlFile, ena_path] = files
                            # save to db & emit signals:
                            (success, err_type, msg) = save_new_allele_to_db(myallele, project, sample_name, 
                                                                            cell_line, filetype, raw_file, 
                                                                            fasta_filename, blastXmlFile,
                                                                            header_data, targetFamily,
                                                                            ena_path, settings, mydb, log)
                            if success:
                                msg = "  - #{}: {}".format(nr, cell_line)
                                successful.append(msg)
                            else:
                                error_dic[nr].append(":".join([err_type, msg]))
        
    # format report:
    report = ""
    if len(successful) > 0:
        report += "Successfully uploaded {} of {} alleles:\n".format(len(successful), num_rows)
        report += "\n".join(successful) + "\n\n"
        
    errors_found = False
    if error_dic:
        errors_found = True
        errors = "Encountered problems in {} of {} alleles:\n".format(len(error_dic), num_rows)
        for nr in sorted(error_dic):
            myerror = "  -#{}: {}\n".format(nr, " AND ".join(error_dic[nr]))
            errors += myerror
        errors += "\nThe problem-alleles were NOT added. Please fix them and try again!"
    else:
        errors = "\nNo problems encountered."
    report += errors
    
    return report, errors_found
                
                
def delete_sample(sample, nr, project, settings, log, parent = None):
    """delete a sample from the database & file system
    """
    # delete from database:
    delete_q_alleles = "delete from alleles where sample_id_int = '{}' and allele_nr = {} and project_name = '{}'".format(sample, nr, project)
    success, _ = db_internal.execute_query(delete_q_alleles, 0, log, "Deleting sample {} allele #{} from ALLELES table".format(sample, nr), "Sample Deletion Error", parent)
    if success:
        log.debug("\t=> Successfully deleted sample from table ALLELES")
    
    more_projects_query = "select project_name from alleles where sample_id_int = '{}'".format(sample)
    success, data = db_internal.execute_query(more_projects_query, 1, log, "Finding more rows with sample {} in ALLELES table".format(sample), "Sample Deletion Error", parent)
    
    single_allele = False
    if success:
        if not data: # sample was only contained in this project and only had one allele
            single_allele = True
            delete_q_samples = "delete from SAMPLES where sample_id_int = '{}'".format(sample)
            success, _ = db_internal.execute_query(delete_q_samples, 0, log, "Deleting sample {} from SAMPLES table".format(sample), "Sample Deletion Error", parent)
            if success:
                log.debug("\t=> Successfully deleted sample from table SAMPLES")
        
        files_q = "select raw_file, fasta, blast_xml, ena_file, ena_response_file, ipd_submission_file from FILES where sample_id_int = '{}' and allele_nr = {}".format(sample, nr)
        success, files = db_internal.execute_query(files_q, 6, log, "Getting files of sample {} #{} from FILES table".format(sample, nr), "Sample Deletion Error", parent)
        if success:
            
            delete_q_files = "delete from FILES where sample_id_int = '{}' and allele_nr = {}".format(sample, nr)
            success, _ = db_internal.execute_query(delete_q_files, 0, log, "Deleting sample {} from FILES table".format(sample), "Sample Deletion Error", parent)
            if success:
                log.debug("\t=> Successfully deleted sample from table FILES")
    
    # delete from disk space:
    log.debug("Attempting to delete sample {} allele #{} of project '{}' from file system...".format(sample, nr, project))
    sample_dir = os.path.join(settings["projects_dir"], project, sample)
    if files:
        for myfile in files[0]:
            if myfile:
                log.debug("\tDeleting {}...".format(myfile))
                try:
                    os.remove(os.path.join(sample_dir, myfile))
                except Exception:
                    log.debug("\t\t=> Could not delete")
    
    if single_allele:
        log.debug("\tDeleting sample dir {}...".format(sample_dir))
        os.removedirs(sample_dir)
    log.debug("=> Sample {} #{} of project {} successfully deleted from database and file system".format(sample, nr, project))


def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
    """generates a random string of length {size},
    using characters given in {chars}
    """
    return ''.join(random.choices(chars, k = size))    


pass
#===========================================================
# main:

def main(settings, log, mydb):
    print (cell_line_looks_ok("t-e-s-t4"))
    
    

if __name__ == "__main__":
    from typeloader_GUI import create_connection, close_connection
    import GUI_login
    log = general.start_log(level="debug")
    log.info("<Start {} V{}>".format(os.path.basename(__file__), __version__))
    settings_dic = GUI_login.get_settings("admin", log)
    mydb = create_connection(log, settings_dic["db_file"])
    main(settings_dic, log, mydb)
    close_connection(log, mydb)
    log.info("<End>")
