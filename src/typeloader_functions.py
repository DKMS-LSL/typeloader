#!/usr/bin/env python3
# -*- coding: cp1252 -*-
'''
Created on 14.03.2018

typeloader_funtions.py

contains calls to TypeLoader_core and handling thereof


@author: Bianca Schoene
'''

# import modules:
import os, shutil
import string, random, time
from collections import defaultdict
from Bio import SeqIO

from src.typeloader_core import (EMBLfunctions as EF, coordinates as COO, backend_make_ena as BME,
                             backend_enaformat as BE, getAlleleSeqsAndBlast as GASB,
                             closestallele as CA, errors)
from src import general, db_internal
# ===========================================================
# parameters:

from src.__init__ import __version__

flatfile_dic = {"function_hla": "antigen presenting molecule",
                "function_kir": "killer-immunoglobulin receptor",
                "productname_hla_i": "MHC class I antigen",
                "productname_hla_ii": "MHC class II antigen",
                "productname_mic": "MHC Class I chain-related gene",
                "productname_hla_i_null": "MHC class I antigen null allele",
                "productname_hla_ii_null": "MHC class II antigen null allele",
                "productname_mic_null": "MHC Class I chain-related gene null allele",
                "productname_kir_long": "Human Killer-cell Immunoglobulin-like Receptor",
                "productname_kir_short": "Killer-cell Immunoglobulin-like Receptor",
                "species": "Homo sapiens"}


# ===========================================================
# classes:

class Allele:
    def __init__(self, gendx_result, gene, name, product, targetFamily, sample_id_int, settings, log,
                 newAlleleName="", partner_allele="", parent=None):
        self.gendx_result = gendx_result
        self.targetFamily = targetFamily
        self.gene = gene
        if targetFamily == "HLA":
            if not gene.startswith("MIC"):
                if "HLA-" not in gene:
                    self.gene = "HLA-" + gene
        self.name = name
        self.product = product
        self.sample_id_int = sample_id_int
        self.settings = settings
        self.log = log
        self.newAlleleName = newAlleleName
        self.partner_allele = partner_allele
        self.null_allele = False
        self.parent = None
        self.make_local_name()

    def make_local_name(self):
        """creates the local name, cell_line and allele_nr of an allele
        """
        self.log.info("Generating local_name and cell_line...")
        query = "select local_name, gene from alleles where sample_id_int = '{}'".format(self.sample_id_int)
        success, data = db_internal.execute_query(query, 2, self.log,
                                                  "retrieving number of alleles for this sample from the database",
                                                  err_type="Database Error", parent=self.parent)
        if success:
            self.allele_nr = len(data) + 1  # number of this allele within this sample
            if self.allele_nr > 1:
                self.log.info("\tThis is allele #{} for this sample!".format(self.allele_nr))

            self.allele_nr_locus = 1
            if data:
                for [_, mygene] in data:
                    if mygene == self.gene:
                        self.allele_nr_locus += 1

            locus = self.gene.replace("HLA-", "").replace("KIR", "")
            self.cell_line = "_".join([self.settings["cell_line_token"], self.sample_id_int])
            self.local_name = "_".join([self.cell_line, locus, str(self.allele_nr_locus)])
            self.log.debug("\tcell_line: {}".format(self.cell_line))
            self.log.debug("\tlocal_name: {}".format(self.local_name))
            self.log.debug("\tallele_nr: {}".format(self.allele_nr))

        else:
            msg = "Could not retrieve existing alleles of sample {}!".format(self.sample_id_int)
            self.log.warning(msg)


# ===========================================================
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
        return (False, "Unknown file format!",
                "Input-file should be .xml or .fasta file. Please use a supported file extension!")

    # save uploaded file to temp dir:
    try:
        temp_raw_file = os.path.join(settings["temp_dir"], os.path.basename(raw_path).replace(" ", "_"))
        if filetype == "FASTA":
            if extension != ".fa":
                temp_raw_file = os.path.splitext(temp_raw_file)[0] + ".fa"
        log.info("Saving file to {}".format(temp_raw_file))
        shutil.copyfile(raw_path, temp_raw_file)
        log.info("\t=> Done!")
    except Exception as E:
        log.exception(E)
        return False, "Could not save file", "An error occurred during upload of '{}'. Please try again!\n\n{}".format(
            raw_path, repr(E))

    # read file:
    try:
        results = GASB.blast_raw_seqs(temp_raw_file, filetype, settings, log)
    except ValueError as E:
        msg = E.args[0]
        if msg.startswith("Fasta"):
            return False, "Invalid FASTA file format", msg
        else:
            return False, "Problem with the FASTA file", msg
    if results[0] == False:  # something went wrong
        return results

    (blastXmlFile, targetFamily, fasta_filename, allelesFilename, header_data, xml_data_dic) = results

    sample_name = None
    if header_data:
        for key in ["SAMPLE_ID_INT", "LIMS-DONOR_ID"]:
            if key in header_data:
                if header_data[key]:
                    sample_name = header_data[key]
                    continue

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
            if allele and allele not in ["NA", "another"] and not ".fa" in allele:  # adjustment for DR2S MIC output
                partners.append(allele)
    header_data["partner_allele"] = " or ".join(partners)

    # set default values:
    if header_data["new_software"] == "DR2S":
        if header_data["lr_data"]:
            header_data["lr_phasing"] = "yes"  # DR2S always produces phased long read data

    # store external sample number if given by parameter (needed for testing):
    if sample_id_ext:
        header_data["Spendernummer"] = sample_id_ext


def remove_other_allele(blast_xml_file, fasta_file, other_allele_name, log, replace=True):
    """removes the non-chosen allele from an XML input file and the generated fasta file
    so it will not later create difficulties (#115)
    """
    log.info("Removing non-chosen partner allele from blast_xml file and generated fasta file...")
    log.debug("\tCleaning fasta file...")
    temp = fasta_file + "1"
    with open(fasta_file, "rU") as f, open(temp, "w") as g:
        for record in SeqIO.parse(f, "fasta"):
            if other_allele_name not in record.id:
                success = SeqIO.write(record, g, 'fasta')
                if success != 1:
                    log.error(f'Error while writing sequence {record.id} to {temp}')

    if replace:
        os.remove(fasta_file)
        shutil.move(temp, fasta_file)

    log.debug("\tCleaning XML file...")
    temp = blast_xml_file + "1"
    with open(blast_xml_file, "r") as f, open(temp, "w") as g:
        header = True
        for line in f:
            if line == "<Iteration>\n":
                header = False
                text = ""
                use_me = True
            if header:
                g.write(line)
            else:
                text += line
                if other_allele_name in line:
                    use_me = False
            if line == "</Iteration>\n":
                if use_me:
                    g.write(text)
                text = ""
        g.write(text)  # write footer

    if replace:
        os.remove(blast_xml_file)
        shutil.move(temp, blast_xml_file)
    log.debug("\t=> Done!")


def process_sequence_file(project, filetype, blastXmlFile, targetFamily, fasta_filename, allelesFilename,
                          header_data, settings, log, incomplete_ok=False):
    log.debug("Processing sequence file...")
    try:
        if filetype == "XML":
            try:
                closestAlleles = CA.get_closest_known_alleles(blastXmlFile, targetFamily, settings, log)
            except errors.IncompleteSequenceWarning as E:
                return False, "Incomplete sequence", E.msg
            except errors.MissingUTRError as E:
                return False, "Missing UTR", E.msg
            except errors.DevianceError as E:
                return False, "Allele too divergent", E.msg

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
                elif geneName.startswith("MIC"):
                    products.append(flatfile_dic["productname_mic"])
                else:
                    products.append(flatfile_dic["productname_hla_i"])

            (gendx_result, gene, name, product) = (genDxAlleleNames[0], geneNames[0], alleleNames[0], products[0])
            allele1 = Allele(gendx_result, gene, name, product, targetFamily, header_data["sample_id_int"], settings,
                             log)

            (gendx_result, gene, name, product) = (genDxAlleleNames[1], geneNames[1], alleleNames[1], products[1])
            allele2 = Allele(gendx_result, gene, name, product, targetFamily, header_data["sample_id_int"], settings,
                             log)

            myalleles = [allele1, allele2]
            ENA_text = ""

        else:  # Fasta-File:
            try:
                annotations = COO.getCoordinates(blastXmlFile, allelesFilename, targetFamily, settings, log,
                                                 incomplete_ok=incomplete_ok)
            except errors.IncompleteSequenceWarning as E:
                return False, "Incomplete sequence", E.msg
            except errors.MissingUTRError as E:
                return False, "Missing UTR", E.msg
            except errors.DevianceError as E:
                return False, "Allele too divergent", E.msg
            except ValueError as E:
                empty_xml = False
                if E.args:
                    msg = E.args[0]
                    if msg == "Your XML file was empty":  #TODO: test this (seems to not be caught correctly)
                        empty_xml = True
                if empty_xml:
                    return False, "BLAST hickup", "The generated blast.xml-file was empty. This was probably a BLAST hickup. Please restart TypeLoader and try again!"
                else:
                    return False, "Input File Error", repr(E)

            alleles = [allele for allele in annotations.keys()]
            # take the first sequence in fasta file
            alleleName = alleles[0]
            pseudogene = ""
            if annotations[alleleName] is None:
                # No BLAST hit at position 1
                msg = "No BLAST hit at position 1"
                log.warning(msg)
                return False, "Problem in XML file", msg
            else:
                extraInformation = annotations[alleleName]["extraInformation"]
                closestAlleleName = annotations[alleleName]["closestAllele"]
                # ToDo: store closest allele in db
                geneName = closestAlleleName.split("*")[0]
                newAlleleName = "%s:new" % closestAlleleName.split(":")[0]

                posHash, sequences = EF.get_coordinates_from_annotation(annotations)

                currentPosHash = posHash[alleleName]
                sequence = sequences[alleleName]
                features = annotations[alleleName]["features"]
                enaPosHash = BME.transform(currentPosHash)
                null_allele, msg = BME.is_null_allele(sequence, enaPosHash)
                if null_allele:
                    log.info(msg)

                    # set productName and function
                gene_tag = "gene"
                if targetFamily == settings["gene_kir"]:  # if KIR
                    productName_FT = geneName + " " + flatfile_dic["productname_kir_short"]
                    productName_DE = flatfile_dic["productname_kir_long"]
                    function = flatfile_dic["function_kir"]
                    if geneName in settings["pseudogenes"].split("|"):
                        log.info("This is a pseudogene!")
                        gene_tag = "gene"
                        pseudogene = '\nFT                   /pseudogene="unprocessed"'
                        null_allele = False
                    else:
                        productName_FT = productName_FT + " null allele" if null_allele else productName_FT
                else:
                    function = flatfile_dic["function_hla"]
                    if geneName.startswith("HLA"):
                        geneName_short = geneName.split("-")[1]
                    else:  # MIC
                        geneName_short = geneName
                    # D ...for DQB, DPB, DRB
                    if geneName_short.startswith("D"):
                        productName_FT = productName_DE = (flatfile_dic["productname_hla_ii"]) \
                            if null_allele == False else (flatfile_dic["productname_hla_ii_null"])  # class 2 gene
                    elif geneName_short.startswith("MIC"):
                        productName_FT = productName_DE = (flatfile_dic["productname_mic"]) \
                            if null_allele == False else (flatfile_dic["productname_mic_null"])  # MIC
                    else:
                        productName_FT = productName_DE = (flatfile_dic["productname_hla_i"]) \
                            if null_allele == False else (flatfile_dic["productname_hla_i_null"])  # class 1 gene

                myallele = Allele("", geneName, newAlleleName, productName_FT, targetFamily,
                                  header_data["sample_id_int"],
                                  settings, log, newAlleleName)
                myallele.null_allele = null_allele
                myalleles = [myallele]
                generalData = BME.make_globaldata(gene_tag=gene_tag, gene=geneName, allele=newAlleleName,
                                                  product_DE=productName_DE, product_FT=productName_FT,
                                                  function=function, species=flatfile_dic["species"],
                                                  seqLen=str(len(sequence)), cellline=myallele.local_name, pseudogene=pseudogene)
                ENA_text = BME.make_header(BE.backend_dict, generalData, enaPosHash, null_allele) + BME.make_genemodel(
                    BE.backend_dict, generalData, enaPosHash, extraInformation, features) + BME.make_footer(
                    BE.backend_dict, sequence)
                # TODO (future): accept multiple sequences from one fasta file
        return True, myalleles, ENA_text
    except Exception as E:
        log.error(E)
        log.exception(E)
        return False, "Error while processing the sequence file", repr(E), None


def make_ENA_file(blastXmlFile, targetFamily, allele, settings, log, incomplete_ok=False):
    """creates ENA file for allele chosen from XML file
    """
    log.debug("Creating ENA text...")
    allelesFilename = os.path.join(settings["dat_path"],
                                   settings["general_dir"],
                                   settings["reference_dir"],
                                   settings["hla_dat"])
    annotations = COO.getCoordinates(blastXmlFile, allelesFilename, targetFamily, settings, log, isENA=True,
                                     incomplete_ok=incomplete_ok)
    posHash, sequences = EF.get_coordinates_from_annotation(annotations)

    currentPosHash = posHash[allele.alleleName]
    sequence = sequences[allele.alleleName]
    enaPosHash = BME.transform(currentPosHash)
    extraInformation = annotations[allele.alleleName]["extraInformation"]
    features = annotations[allele.alleleName]["features"]

    if allele.geneName in settings["pseudogenes"].split("|"):
        allele.null_allele = False  # whole locus is already pseudogene
    else:
        allele.null_allele, msg = BME.is_null_allele(sequence, enaPosHash)
        if allele.null_allele:
            log.info(msg)
        allele.productName_FT = allele.productName_FT + " null allele" if allele.null_allele else allele.productName_FT

    generalData = BME.make_globaldata(gene_tag="gene",
                                      gene=allele.geneName,
                                      allele=allele.newAlleleName,
                                      product_DE=allele.productName_DE,
                                      product_FT=allele.productName_FT,
                                      function=flatfile_dic["function_hla"],
                                      species=flatfile_dic["species"],
                                      seqLen=str(len(sequence)),
                                      cellline=allele.local_name)
    ENA_text = BME.make_header(BE.backend_dict, generalData, enaPosHash, allele.null_allele)
    ENA_text += BME.make_genemodel(BE.backend_dict, generalData, enaPosHash,
                                   extraInformation, features)
    ENA_text += BME.make_footer(BE.backend_dict, sequence)
    ENA_text = ENA_text.strip()

    return ENA_text


def move_files_to_sample_dir(project, sample_name, local_name, filetype,
                             temp_raw_file, blastXmlFile, fasta_filename,
                             settings, log):
    """creates sample_dir and moves all sequence files there,
    renames them to cell line
    """
    project_dir = os.path.join(settings["projects_dir"], project)
    sample_dir = os.path.join(project_dir, sample_name)
    if not os.path.isdir(sample_dir):
        os.makedirs(sample_dir)
    log.debug("\tMoving files to sample_dir: {}".format(sample_dir))
    raw_file = general.move_rename_file(temp_raw_file, sample_dir, local_name)
    blastXmlFile = general.move_rename_file(blastXmlFile, sample_dir, local_name)
    if filetype == "XML":
        fasta_filename = general.move_rename_file(fasta_filename, sample_dir, local_name)
    else:
        fasta_filename = raw_file
    return sample_dir, raw_file, fasta_filename, blastXmlFile


def save_new_allele(project, sample_name, local_name, ENA_text,
                    filetype, temp_raw_file, blastXmlFile, fasta_filename,
                    settings, log):
    """saves files of new target allele and writes ENA file
    """
    log.debug("Saving files for allele {}...".format(local_name))
    try:
        # create sample folder & move files there:
        results = move_files_to_sample_dir(project, sample_name, local_name,
                                           filetype, temp_raw_file, blastXmlFile, fasta_filename,
                                           settings, log)
        (sample_dir, raw_file, fasta_filename, blastXmlFile) = results
    except Exception as E:
        log.error(E)
        log.exception(E)
        msg = "Could not save the sample's files\n\n{}".format(repr(E))
        return (False, "ENA file creation error", msg, None)

    try:
        # write ENA file:
        ena_path = os.path.join(sample_dir, local_name + ".ena.txt")
        log.info("\tSaving this allele of sample {} to {}".format(sample_name, ena_path))
        with open(ena_path, "w") as g:
            g.write(ENA_text.strip())

    except Exception as E:
        log.error(E)
        log.exception(E)
        msg = "Could not write the ENA file for {}\n\n{}".format(local_name, repr(E))
        return (False, "ENA file creation error", msg, None)

    files = [raw_file, fasta_filename, blastXmlFile, ena_path]
    return (True, None, None, files)


def save_new_allele_to_db(allele, project,
                          filetype, raw_file, fasta_filename, blastXmlFile,
                          header_data, targetFamily,
                          ena_path, settings, mydb, log):
    """save new allele to internal database
    """
    try:
        log.info("Saving allele {} to database...".format(allele.newAlleleName))

        # get numbers to increment from database:
        query1 = "select count(*) from alleles where project_name = '{}'".format(project)
        success, data = db_internal.execute_query(query1, 1, log,
                                                  "retrieving number of alleles for this project from the database",
                                                  err_type="Database Error", parent=None)
        if success:
            try:
                project_nr = data[0][0] + 1
            except IndexError:
                project_nr = 1
        else:
            log.warning("Could not retrieve existing alleles of project {}!".format(project))
            return (False, False, False)

        # prepare data:
        if targetFamily == "HLA":
            reference = "IPD-IMGT/HLA"
        else:
            reference = "IPD-KIR"
        if not allele.partner_allele:
            allele.partner_allele = header_data["partner_allele"]
        if allele.null_allele:
            null_allele = 'yes'
        else:
            null_allele = 'no'
        update_queries = []
        # update ALLELES table:
        update_alleles_query = """INSERT INTO alleles 
        (sample_id_int, allele_nr, project_name, project_nr, local_name, GENE, 
        Goal, Allele_status, Lab_Status, 
        null_allele,
        target_allele, partner_allele, reference_database,
        long_read_data, long_read_phasing, long_read_technology,
        short_read_data, short_read_phasing, short_read_technology,
        New_genotyping_software, New_software_version, New_genotyping_date, 
        kommentar, Database_version, upload_date)
        VALUES 
        ('{}', '{}', '{}', {}, '{}', '{}', 
        'novel', 'ENA-ready', 'completed', 
        '{}',
        '{}', '{}', '{}',
        '{}', '{}', '{}',
        '{}', '{}', '{}',
        '{}', '{}', '{}', 
        '{}', '{}', '{}')
        """.format(allele.sample_id_int, allele.allele_nr, project, project_nr, allele.local_name, allele.gene,
                   null_allele,
                   allele.newAlleleName, allele.partner_allele, reference,
                   header_data["lr_data"], header_data["lr_phasing"], header_data["lr_tech"],
                   header_data["sr_data"], header_data["sr_phasing"], header_data["sr_tech"],
                   header_data["new_software"], header_data["new_version"], header_data["new_timestamp"],
                   header_data["comment"], header_data["ref_version"], general.timestamp('%Y-%m-%d'))
        update_queries.append(update_alleles_query)

        # update SAMPLES table:
        query4 = "select count(*) from samples where SAMPLE_ID_INT = '{}'".format(allele.sample_id_int)
        success, data = db_internal.execute_query(query4, 1, log,
                                                  "checking if sample already known",
                                                  err_type="Database Error", parent=None)
        if success:
            if data != [[0]]:  # if sample already known, don't re-enter it
                pass
            else:
                update_samples_query = """INSERT INTO samples
                (SAMPLE_ID_INT, SAMPLE_ID_EXT, CELL_LINE) values ('{}', '{}', '{}')
                """.format(allele.sample_id_int, header_data["Spendernummer"], allele.cell_line)
                update_queries.append(update_samples_query)
        else:
            return (False, False, False)

        # update FILES table:
        update_files_query = """INSERT INTO files
        (Sample_ID_int, local_name, allele_nr, project, raw_file_type, raw_file, fasta, 
        blast_xml, ena_file) values 
        ('{}', '{}', {}, '{}', '{}', '{}', '{}', 
        '{}', '{}')
        """.format(allele.sample_id_int, allele.local_name, allele.allele_nr, project, filetype,
                   os.path.basename(raw_file), os.path.basename(fasta_filename),
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
        msg = "An error occurred during the attempt to save this allele to the database. (See below)\nThe allele was not saved!\n\n{}".format(
            repr(E))
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
                if len(row) > 6:
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
                        incomplete_ok = row[6].strip()
                        if incomplete_ok.lower() in ["true", "wahr", "ok", "yes"]:
                            incomplete_ok = True
                        else:
                            incomplete_ok = False
                        if not err:
                            myallele = [nr, sample_id_int, sample_id_ext, mypath, customer, incomplete_ok]
                            alleles.append(myallele)
    log.info("\t=> {} processable alleles found in {} rows".format(len(alleles), i))
    return alleles, error_dic, i


def upload_new_allele_complete(project_name, sample_id_int, sample_id_ext, raw_path, customer,
                               settings, mydb, log, incomplete_ok=False):
    """adds one new target sequence to TypeLoader
    """
    log.info("Uploading {} to project {}...".format(sample_id_int, project_name))
    results = upload_parse_sequence_file(raw_path, settings, log)
    if results[0] == False:  # something went wrong
        return False, "{}: {}".format(results[1], results[2])
    log.debug("\t=> success")

    (_, _, filetype, temp_raw_file, blastXmlFile,
     targetFamily, fasta_filename, allelesFilename, header_data) = results
    reformat_header_data(header_data, sample_id_ext, log)
    if customer:
        header_data["Customer"] = customer

    # process raw file:
    sample_name = sample_id_int
    header_data["sample_id_int"] = sample_id_int
    results = process_sequence_file(project_name, filetype, blastXmlFile,
                                    targetFamily, fasta_filename, allelesFilename,
                                    header_data, settings, log, incomplete_ok=incomplete_ok)
    if not results[0]:  # something went wrong
        return False, "{}: {}".format(results[1], results[2])
    log.debug("\t=> success")

    (_, myalleles, ENA_text) = results
    myallele = myalleles[0]
    myallele.sample_id_int = sample_id_int
    myallele.make_local_name()
    # save allele files:
    results = save_new_allele(project_name, sample_name, myallele.local_name, ENA_text,
                              filetype, temp_raw_file, blastXmlFile, fasta_filename,
                              settings, log)
    (success, err_type, msg, files) = results

    if not success:
        return False, "{}: {}".format(err_type, msg)

    [raw_file, fasta_filename, blastXmlFile, ena_path] = files
    # save to db & emit signals:
    (success, err_type, msg) = save_new_allele_to_db(myallele, project_name,
                                                     filetype, raw_file,
                                                     fasta_filename, blastXmlFile,
                                                     header_data, targetFamily,
                                                     ena_path, settings, mydb, log)
    if success:
        log.debug("Allele uploaded successfully")
        return True, myallele.local_name
    else:
        return False, "{}: {}".format(err_type, msg)


def bulk_upload_new_alleles(csv_file, project, settings, mydb, log):
    """performs bulk uploading, parsing and saving of new target alleles
    specified in a .csv file 
    """
    log.info("Starting bulk upload from file {}...".format(csv_file))
    alleles, error_dic, num_rows = parse_bulk_csv(csv_file, settings, log)
    successful = []
    for allele in alleles:
        [nr, sample_id_int, sample_id_ext, raw_path, customer, incomplete_ok] = allele
        log.info("Uploading #{}: {}...".format(nr, sample_id_int))
        success, msg = upload_new_allele_complete(project, sample_id_int, sample_id_ext, raw_path, customer, settings,
                                                  mydb, log, incomplete_ok=incomplete_ok)
        if success:
            successful.append("  - #{}: {}".format(nr, msg))
        else:
            if msg.startswith("Incomplete sequence"):
                msg = msg.replace("\n", " ").split("!")[0] + "!"
            error_dic[nr].append(msg)

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
            myerror = "  - #{}: {}\n".format(nr, " AND ".join(error_dic[nr]))
            errors += myerror
        errors += "\nThe problem-alleles were NOT added. Please fix them and try again!"
    else:
        errors = "\nNo problems encountered."
    report += errors

    return report, errors_found


def delete_sample(sample, nr, project, settings, log, parent=None):
    """delete a sample from the database & file system
    """
    log.info(f"Deleting {sample} allele #{nr} from project {project}...")
    log.debug("Deleting from database...")
    # delete from database:
    delete_q_alleles = f"""delete from alleles where sample_id_int = '{sample}' and allele_nr = {nr} 
                        and project_name = '{project}'"""
    success, _ = db_internal.execute_query(delete_q_alleles, 0, log,
                                           f"Deleting sample {sample} allele #{nr} from ALLELES table",
                                           "Sample Deletion Error", parent)
    if success:
        log.debug("\t=> Successfully deleted sample from table ALLELES")

    more_projects_query = f"select project_name from alleles where sample_id_int = '{sample}'"
    success, data = db_internal.execute_query(more_projects_query, 1, log,
                                              f"Finding more rows with sample {sample} in ALLELES table",
                                              "Sample Deletion Error", parent)

    single_allele = False
    files = None
    if success:
        if not data:  # sample was only contained in this project and only had one allele
            single_allele = True
            delete_q_samples = "delete from SAMPLES where sample_id_int = '{}'".format(sample)
            success, _ = db_internal.execute_query(delete_q_samples, 0, log,
                                                   f"Deleting sample {sample} from SAMPLES table",
                                                   "Sample Deletion Error", parent)
            if success:
                log.debug("\t=> Successfully deleted sample from table SAMPLES")

        files_q = """select raw_file, fasta, blast_xml, ena_file, ena_response_file, ipd_submission_file from FILES 
                    where sample_id_int = '{}' and allele_nr = {}""".format(sample, nr)
        success, files = db_internal.execute_query(files_q, 6, log,
                                                   f"Getting files of sample {sample} #{nr} from FILES table",
                                                   "Sample Deletion Error", parent)
        if success:

            delete_q_files = f"delete from FILES where sample_id_int = '{sample}' and allele_nr = {nr}"
            success, _ = db_internal.execute_query(delete_q_files, 0, log,
                                                   f"Deleting sample {sample} from FILES table",
                                                   "Sample Deletion Error", parent)
            if success:
                log.debug("\t=> Successfully deleted sample from table FILES")

    # delete from disk space:
    log.debug("Deleting from file system...")
    sample_dir = os.path.join(settings["projects_dir"], project, sample)
    if files:
        for myfile in files[0]:
            if myfile:
                log.debug(f"\tDeleting {myfile}...")
                try:
                    os.remove(os.path.join(sample_dir, myfile))
                except Exception:
                    log.debug("\t\t=> Could not delete")

    if single_allele:
        log.debug(f"\tDeleting sample dir {sample_dir}...")
        try:
            os.removedirs(sample_dir)
        except Exception as E:
            log.exception(E)
    log.debug(
        f"=> Sample {sample} #{nr} of project {project} successfully deleted from database and file system")


def delete_all_samples_from_project(project_name, settings, log, parent=None):
    log.info("Deleting all samples from project {}...".format(project_name))
    query = "select sample_id_int, allele_nr from ALLELES where project_name = '{}'".format(project_name)
    _, data = db_internal.execute_query(query, 2, log, "Getting samples from ALLELES table", "Sample Deletion Error",
                                        parent)
    for [sample_id_int, nr] in data:
        delete_sample(sample_id_int, nr, project_name, settings, log)


def id_generator(size=8, chars=string.ascii_uppercase + string.digits):
    """generates a random string of length {size},
    using characters given in {chars}
    """
    return ''.join(random.choices(chars, k=size))


def create_ENA_filenames(project_name, ENA_ID, settings, log):
    """creates the filenames for all files needed for ENA sequence submission,
    returns them as a dict
    """
    log.debug("Creating project filenames for ENA submission...")

    curr_time = time.strftime("%Y%m%d%H%M%S")
    analysis_alias = ENA_ID + "_" + curr_time
    project_dir = os.path.join(settings["projects_dir"], project_name)
    file_start = os.path.join(project_dir, analysis_alias)
    concat_FF_zip = file_start + "_flatfile.txt.gz"
    manifest_filename = file_start + "_manifest.txt"

    file_dic = {"concat_FF_zip": concat_FF_zip,
                "manifest": manifest_filename,
                "project_dir": project_dir}

    log.debug("\t=> done")
    return file_dic, curr_time, analysis_alias


def submit_sequences_to_ENA_via_CLI(project_name, ENA_ID, analysis_alias, curr_time, samples, input_files, file_dic,
                                    settings, log):
    """handles submission of sequences via ENA's Webin-CLI & creation of all files for this
    """
    log.info("Submitting sequences to ENA...")
    submission_alias = analysis_alias + "_filesub"

    if len(input_files) == 0:
        log.warning("No files were selected for Submission!")
        return False, False, "No files selected", "Please select at least one file for submission!", []

    ## 1. create a concatenated flatfile
    log.debug("Concatenating flatfiles...")
    concat_successful, line_dic = EF.concatenate_flatfile(input_files, file_dic["concat_FF_zip"], log)
    if not concat_successful:
        log.error("Concatenation wasn't successful")
        return False, False, "Concatenation problem", "Concatenated file is empty :-(", []

    ## 2. create a manifest file
    log.debug("Creating submission manifest...")
    try:
        EF.make_manifest(file_dic["manifest"], ENA_ID, submission_alias, file_dic["concat_FF_zip"], log)
    except Exception as E:
        log.error("Could not create manifest file!")
        log.exception(E)
        return False, False, "Manifest file problem", "Could not create the manifest file for ENA submission: {}".format(
            repr(E)), []

    ## 3. validate files via CLI
    log.debug("Validating submission files using ENA's Webin-CLI...")
    cmd_string, msg = EF.make_ENA_CLI_command_string(file_dic["manifest"], file_dic["project_dir"], settings, log)

    if not cmd_string:
        log.error("Could not generate command for Webin-CLI!")
        return False, False, "Webin-CLI command problem", msg, []

    log.debug("Validating command and files...")

    validate_cmd = cmd_string + " -validate"
    success, ENA_response, _, problem_samples = EF.handle_webin_CLI(validate_cmd, "validate", submission_alias,
                                                                    file_dic["project_dir"],
                                                                    line_dic, log)
    if not success:
        log.error("Validation by ENA's Webin-CLI failed!")
        log.error(ENA_response)
        print(ENA_response)
        return [ENA_response], False, "ENA validation error", ENA_response, problem_samples

    log.debug("\t=> looking good")

    ## 4. submit files via CLI
    log.debug("Submitting files...")
    submission_cmd = cmd_string + " -submit"
    successful_transmit, ENA_response, analysis_accession_number, problem_samples = EF.handle_webin_CLI(submission_cmd,
                                                                                                        "submit",
                                                                                                        submission_alias,
                                                                                                        file_dic[
                                                                                                            "project_dir"],
                                                                                                        line_dic, log)
    submission_accession_number = None  # used to be contained in ENA's reply, but has been deprecated with the start of Webin-CLI

    if not successful_transmit:
        msg = "Submission to ENA failed even though validation passed"
        log.error(msg)
        log.error(ENA_response)
        # FIXME: we used to roll back the submission, to not SPAM the server. Can we still do this?
        return [ENA_response], False, "ENA submission error", "ENA submission error {}:\n\n{}".format(msg,
                                                                                                      ENA_response), problem_samples

    log.debug("\t=> submission successful (submission ID = {})".format(analysis_accession_number))
    ans_time = time.strftime("%Y%m%d%H%M%S")
    ena_results = (analysis_alias, curr_time, ans_time,
                   analysis_accession_number, submission_accession_number, ENA_response)
    return ena_results, True, None, None, problem_samples


pass


# ===========================================================
# main:

def main(settings, log, mydb):
    project_name = "20200128_ADMIN_DRB1_test124"
    # sample_id_int = 'ID13107882'
    sample_id_int = "ID_should_not_pass"
    sample_id_ext = "test3"
    # raw_path = r"H:\Projekte\Bioinformatik\Typeloader Projekt\Issues\124_DRB1_incorrect_confirmation\end_del3.fa"
    customer = "DKMS"
    raw_path = r"H:\Projekte\Bioinformatik\Typeloader Projekt\Issues\125_weird_X_allele\1373616_A.fa"
    incomplete_ok = False
    upload_new_allele_complete(project_name, sample_id_int, sample_id_ext, raw_path, customer, settings, mydb, log, incomplete_ok)
    log.debug("--------------------------------------------")
    delete_sample(sample_id_int, 1, project_name, settings, log)

    # from src.typeloader_core import make_imgt_files as MIF
    # from src.GUI_forms_submission_IPD import TargetAllele
    # results = MIF.make_imgt_data(r"\\nasdd12\daten\data\Typeloader\admin\projects\20200128_ADMIN_DRB1_test124",
    #                              [('ID13107882', 'DKMS-LSL_ID13107882_DRB1_9', '')],
    #                              {'DKMS-LSL_ID13107882_DRB1_9': {'blast_xml': 'DKMS-LSL_ID13107882_DRB1_9.blast.xml',
    #                                                              'ena_file': 'DKMS-LSL_ID13107882_DRB1_9.ena.txt'}},
    #                              {'DKMS-LSL_ID13107882_DRB1_9': TargetAllele(gene='HLA-DRB1',
    #                                                                          target_allele='HLA-DRB1*01:new',
    #                                                                          partner_allele='HLA-DRB1*15:02:01:01 or 01:01:01 or list(NULL)')},
    #                              {'DKMS-LSL_ID13107882_DRB1_9': '96901LSB'},
    #                              ,
    #                              r"\\nasdd12\daten\data\Typeloader\admin\temp\fake_befunde.csv",
    #                              settings, log)

    # project_dir = r"\\nasdd12\daten\data\Typeloader\admin\projects\20200213_ADMIN_HLA-A_test124"
    #
    # allele = "DKMS-LSL_ID11273358_DRB1_1"
    # locus = "HLA-DRB1"
    # samples = [('ID11273358', allele, '')]
    # file_dic = {f'{allele}': {'blast_xml': f'{allele}.blast.xml',
    #                           'ena_file': f'{allele}.ena.txt'}}
    # allele_dic = {f'{allele}': TargetAllele(gene=locus,
    #                                         target_allele=f'{locus}*01:new',
    #                                         partner_allele=f'{locus}*01:01:01:01')}
    # cellEnaIdMap = {f'{allele}': '96901LSB'}
    # geneMapENA = {f'{allele}': locus}
    # befund_csv_file = r"\\nasdd12\daten\data\Typeloader\admin\temp\fake_befunde.csv"
    # results = MIF.make_imgt_data(project_dir, samples, file_dic, allele_dic, cellEnaIdMap, geneMapENA, befund_csv_file,
    #                              settings, log)
    #
    # try:
    #     print(results[0]['DKMS10009742'].split("CC   ")[1].split("\n")[0])
    # except:
    #     print("Could not find IPD file for this submission number!")
    #     print(results[0])




if __name__ == "__main__":
    from src.typeloader_GUI import create_connection, close_connection
    import GUI_login

    log = general.start_log(level="debug")
    log.info("<Start {} V{}>".format(os.path.basename(__file__), __version__))
    settings_dic = GUI_login.get_settings("admin", log)
    mydb = create_connection(log, settings_dic["db_file"])
    main(settings_dic, log, mydb)
    close_connection(log, mydb)
    log.info("<End>")
