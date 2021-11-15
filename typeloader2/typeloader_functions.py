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

from typeloader_core import (EMBLfunctions as EF, coordinates as COO, backend_make_ena as BME,
                             backend_enaformat as BE, getAlleleSeqsAndBlast as GASB,
                             closestallele as CA, errors, update_reference)
import general, db_internal

# ===========================================================
# parameters:

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
                 newAlleleName="", partner_allele="", parent=None, existing_values=None):
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
        if existing_values:
            (self.allele_nr, self.local_name) = existing_values
            self.cell_line = "_".join(self.local_name.split("_")[:2])
        else:
            self.make_local_name()

    def get_lowest_free_nr(self, highest_possible_nr, used_nrs):
        """returns lowest non-taken number between 1 and highest_possible_nr that is not contained in used_nrs
        """
        for n in range(1, highest_possible_nr + 1):
            if n not in used_nrs:
                return n

    def make_local_name(self):
        """creates the local name, cell_line and allele_nr of an allele
        """
        self.log.info("Generating local_name and cell_line...")
        query = f"""select local_name, allele_nr, gene from alleles 
                where sample_id_int = '{self.sample_id_int}'
                order by gene, allele_nr"""
        success, data = db_internal.execute_query(query, 3, self.log,
                                                  "retrieving number of alleles for this sample from the database",
                                                  err_type="Database Error", parent=self.parent)
        if success:
            if data:
                allele_nrs = [nr for [_, nr, _] in data]
                highest_possible_allele_nr = max(allele_nrs) + 1
                self.allele_nr = self.get_lowest_free_nr(highest_possible_allele_nr, allele_nrs)

                same_gene_alleles = [int(local_name.split("_")[-1]) for [local_name, _, gene] in data if
                                     gene == self.gene]
                self.allele_nr_locus = self.get_lowest_free_nr(highest_possible_allele_nr, same_gene_alleles)

                self.log.info(f"\tThis is allele #{self.allele_nr} for this sample "
                              f"and allele #{self.allele_nr_locus} for this locus!")
            else:
                self.allele_nr = 1
                self.allele_nr_locus = 1

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


def perform_reference_update(db_name, reference_local_path, blast_path, log, version=None):
    """call trigger reference update of a database

    :param db_name: HLA or KIR
    :param reference_local_path: path to 'reference_data' dir
    :param blast_path: path to BLASTN
    :param log: logger instance
    :return: success (bool), error_type (str or None), message (str)
    """
    db_name = db_name.lower()
    if db_name not in ["hla", "kir"]:
        return False, "Unknown reference type", \
               f"'{db_name}' is an unknown reference. Please select 'hla' or 'kir'!"

    blast_dir = os.path.dirname(blast_path)
    try:
        success, update_msg = update_reference.update_database(db_name, reference_local_path, blast_dir, log,
                                                               version=version)
    except Exception as E:
        log.exception("Reference update failed!")
        general.play_sound(log)
        msg = f"Could not update the reference database(s). Please try again!\n\nError: {repr(E)}"
        return False, "Reference update failed", msg

    if success:
        err = None
    else:
        err = "Reference update failed"

    return success, err, update_msg


def update_curr_versions(settings, log):
    """gets the current version of the reference databases
    """
    log.info(f"Getting current database versions...")
    reference_path = os.path.join(settings["root_path"], settings["general_dir"], settings["reference_dir"])
    db_versions = {}
    for db_name in ["hla", "KIR"]:
        version_file = os.path.join(reference_path, f"curr_version_{db_name}.txt")
        try:
            with open(version_file, "r") as f:
                version = f.read().strip()
        except IOError:
            version = None
        db_name = db_name.upper()
        log.info(f"\tcurrent {db_name} version is {version}")
        db_versions[db_name] = version

    settings["db_versions"] = db_versions


def toggle_project_status(proj_name, curr_status, log, values=["Open", "Closed"],
                          texts=["Close Project", "Reopen Project"], parent=None):
    """toggles the status of a given project between 'Open' and 'Closed';
    returns success (bool) + the new status (str)
    """
    # ToDO: handle "status toggling" if current status unknown
    if curr_status == values[0]:
        new_ix = 1
    else:
        new_ix = 0
    new_value = values[new_ix]
    log.info("Changing state of project '{}' to '{}'...".format(proj_name, new_value))
    query = f"update PROJECTS set project_status = '{new_value}' where project_name = '{proj_name}'"
    success, _ = db_internal.execute_query(query, 0, log, "Updating project status", "Update error", parent)
    if success:
        log.info(f"\t=> Success (emitting data_changed = '{proj_name}')")
        return success, new_value, new_ix
    else:
        log.warning(f"Could not change status of project {proj_name}!")
        return success, curr_status, 0


def upload_parse_sequence_file(raw_path, settings, log, use_given_reference=False):
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
        results = GASB.blast_raw_seqs(temp_raw_file, filetype, settings, log,
                                      use_given_reference=use_given_reference)
    except ValueError as E:
        msg = E.args[0]
        if msg.startswith("Fasta"):
            return False, "Invalid FASTA file format", msg
        else:
            return False, "Problem with the FASTA file", msg
    except errors.UnknownXMLFormatError as E:
        return False, "Unsupported XML file format", E.msg

    if results[0] == False:  # something went wrong
        return results

    (blastXmlFile, targetFamily, fasta_filename, allelesFilename,
     header_data, xml_data_dic) = results

    sample_name = None
    if header_data:
        for key in ["SAMPLE_ID_INT", "LIMS_DONOR_ID"]:
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
        records = list(SeqIO.parse(f, "fasta"))
        if len(records) == 1:  # only one allele present
            log.debug("\t\t=> only one allele found, no cleaning necessary.")
            return
        for record in records:
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


def process_sequence_file(project, filetype, blastXmlFile, targetFamily, fasta_filename,
                          allelesFilename, header_data, settings, log, incomplete_ok=False, startover=False):
    log.debug("Processing sequence file...")
    if startover:
        allele_nr = startover["allele_nr"]
        local_name = startover["local_name"]
        existing_values = (allele_nr, local_name)
    else:
        existing_values = None
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
            except OverflowError as E:
                return False, "Too many possible alignments", str(E)
            except ValueError:
                return False, "Something in the reference seems not up-to-date.\n" \
                              "Please update your reference via Options => Refresh Reference and try again."

            genDxAlleleNames = list(closestAlleles.keys())
            for allele in genDxAlleleNames[:2]:
                if closestAlleles[allele] == 0:
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
                             log, existing_values=existing_values)

            if len(genDxAlleleNames) > 1:
                (gendx_result, gene, name, product) = (genDxAlleleNames[1], geneNames[1],
                                                       alleleNames[1], products[1])
                allele2 = Allele(gendx_result, gene, name, product, targetFamily,
                                 header_data["sample_id_int"], settings, log)
            else:
                allele2 = Allele("", "", "", "", "", header_data["sample_id_int"], settings, log,
                                 existing_values=existing_values)

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
                    if msg == "Your XML file was empty":  # TODO: test this (seems to not be caught correctly)
                        empty_xml = True
                if empty_xml:
                    return False, "BLAST hickup", "The generated blast.xml-file was empty. This was probably a BLAST " \
                                                  "hickup. Please refresh your reference database " \
                                                  "or restart TypeLoader, and then try again!"
                else:
                    return False, "Input File Error", repr(E)
            except OverflowError as E:
                return False, "Too many possible alignments", str(E)
            alleles = [allele for allele in annotations.keys()]
            # take the first sequence in fasta file
            alleleName = alleles[0]
            pseudogene = ""
            if annotations[alleleName] is None:
                # No BLAST hit at position 1
                msg = "No BLAST hit at position 1"
                log.warning(msg)
                return False, "Problem in Fasta file", msg
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
                    if geneName == "HLA-E" and msg == "Attention! Number of exon bases not divisible by 3  => null allele!":
                        null_allele = False
                        msg2 = "Null-allele-check for 'number of exon bases must be divisable by 3' is currently "
                        msg2 += "disabled for HLA-E (#162)"
                        log.info(msg2)
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
                                  settings, log, newAlleleName, existing_values=existing_values)
                myallele.null_allele = null_allele
                myalleles = [myallele]
                db_name = targetFamily.upper()
                generalData = BME.make_globaldata(gene_tag=gene_tag, gene=geneName, allele=newAlleleName,
                                                  product_DE=productName_DE, product_FT=productName_FT,
                                                  function=function, species=flatfile_dic["species"],
                                                  seqLen=str(len(sequence)), cellline=myallele.local_name,
                                                  pseudogene=pseudogene, TL_version=settings["TL_version"],
                                                  db_name=db_name, db_version=settings["db_versions"][db_name])
                ENA_text = BME.make_header(BE.backend_dict, generalData, enaPosHash, null_allele) + BME.make_genemodel(
                    BE.backend_dict, generalData, enaPosHash, extraInformation, features) + BME.make_footer(
                    BE.backend_dict, sequence)
                # TODO (future): accept multiple sequences from one fasta file
        return True, myalleles, ENA_text
    except Exception as E:
        log.error(E)
        log.exception(E)
        return False, "Error while processing the sequence file", repr(E)


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
            if allele.geneName == "HLA-E" and msg == "Attention! Number of exon bases not divisible by 3  => null allele!":
                allele.null_allele = False
                msg2 = "Null-allele-check for 'number of exon bases must be divisable by 3' is currently "
                msg2 += "disabled for HLA-E (#162)"
                log.info(msg2)
        if allele.null_allele:
            log.info(msg)
        allele.productName_FT = allele.productName_FT + " null allele" if allele.null_allele else allele.productName_FT

    db_name = targetFamily.upper()
    generalData = BME.make_globaldata(gene_tag="gene",
                                      gene=allele.geneName,
                                      allele=allele.newAlleleName,
                                      product_DE=allele.productName_DE,
                                      product_FT=allele.productName_FT,
                                      function=flatfile_dic["function_hla"],
                                      species=flatfile_dic["species"],
                                      seqLen=str(len(sequence)),
                                      cellline=allele.local_name,
                                      TL_version=settings["TL_version"],
                                      db_name=db_name,
                                      db_version=settings["db_versions"][db_name])
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
                    filetype, temp_raw_file, blastXmlFile, fasta_filename, restricted_db_path,
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

    if restricted_db_path:
        log.debug("Saving restricted database into sample's directory...")
        target_dir = os.path.join(sample_dir, f"{local_name}_restricted_db")
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        for (dirpath, subdirs, files) in os.walk(os.path.join(settings["temp_dir"],
                                                              "restricted_db")):
            for f in files:
                myfile = os.path.join(dirpath, f)
                shutil.move(myfile, os.path.join(target_dir, f))

    files = [raw_file, fasta_filename, blastXmlFile, ena_path]
    return (True, None, None, files)


def save_new_allele_to_db(allele, project,
                          filetype, raw_file, fasta_filename, blastXmlFile,
                          header_data, targetFamily,
                          ena_path, restricted_alleles, settings, mydb, log, startover=False):
    """save new allele to internal database
    """
    try:
        log.info("Saving allele {} to database...".format(allele.newAlleleName))
        startover_allele = False
        if startover:
            startover_allele = True
        # get numbers to increment from database:
        query1 = "select max(project_nr) from alleles where project_name = '{}'".format(project)
        success, data = db_internal.execute_query(query1, 1, log,
                                                  "retrieving number of alleles for this project from the database",
                                                  err_type="Database Error", parent=None)
        if success:
            if data == [['']]:
                project_nr = 1
            else:
                project_nr = data[0][0] + 1
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

        for key in header_data:
            if not header_data[key]:
                header_data[key] = ""

        update_queries = []
        if restricted_alleles:
            msg = f"Uploaded using a reference restricted to {' & '.join(restricted_alleles)}"
            if header_data["comment"]:
                header_data["comment"] = msg + " ; " + header_data["comment"]
            else:
                header_data["comment"] = msg
        # update ALLELES table:

        startover_keys = ["ena_submission_id", "ena_acception_date", "ena_accession_nr",
                          "ipd_submission_id", "ipd_submission_nr", "hws_submission_nr",
                          "kommentar"]
        if startover_allele:
            allele.allele_nr = startover["allele_nr"]
            project_nr = startover["project_nr"]
            allele.local_name = startover["local_name"]
            delete_query = f"delete from alleles where local_name = '{allele.local_name}'"
            update_queries.append(delete_query)
        else:
            startover = {}
            for key in startover_keys:
                startover[key] = None

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

        if startover:
            update_me = []
            for key in startover_keys:
                if startover[key]:
                    update_me.append(key)

            if update_me:
                update_query = "update alleles set "
                for key in update_me:
                    update_query += f"{key} = '{startover[key]}', "
                update_query = update_query[:-2]  # remove trailing comma
                update_query += f" where local_name = '{startover['local_name']}'"
                update_queries.append(update_query)

        # update SAMPLES table:
        query4 = "select count(*) from samples where SAMPLE_ID_INT = '{}'".format(allele.sample_id_int)
        success, data = db_internal.execute_query(query4, 1, log,
                                                  "checking if sample already known",
                                                  err_type="Database Error", parent=None)
        if success:
            if data != [[0]] or startover_allele:  # if sample already known, don't re-enter it
                pass
            else:
                update_samples_query = """INSERT INTO samples
                (SAMPLE_ID_INT, SAMPLE_ID_EXT, CELL_LINE) values ('{}', '{}', '{}')
                """.format(allele.sample_id_int, header_data["Spendernummer"], allele.cell_line)
                update_queries.append(update_samples_query)
        else:
            return (False, False, False)

        # update FILES table:
        if startover_allele:
            delete_files = f"""delete from files where local_name = '{allele.local_name}'"""
            update_queries.append(delete_files)

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


def handle_new_allele_parsing(project_name, sample_id_int, sample_id_ext, raw_path, customer,
                              settings, log, use_restricted_db=False):
    """handles step one of the uploading of one new allele to TL;
    called by NewAlleleForm and upload_new_allele_complete()
    """
    log.info("Uploading {} to project {}...".format(sample_id_int, project_name))
    results = upload_parse_sequence_file(raw_path, settings, log,
                                         use_given_reference=use_restricted_db)
    if not results[0]:  # something went wrong
        return False, "{}: {}".format(results[1], results[2])
    log.debug("\t=> success")

    (_, sample_name, filetype, temp_raw_file, blastXmlFile,
     targetFamily, fasta_filename, allelesFilename, header_data) = results
    reformat_header_data(header_data, sample_id_ext, log)
    if customer:
        header_data["Customer"] = customer
    if sample_id_int:
        header_data["sample_id_int"] = sample_id_int
    if sample_id_ext:
        header_data["sample_id_ext"] = sample_id_ext

    results = (header_data, filetype, sample_name, targetFamily,
               temp_raw_file, blastXmlFile, fasta_filename, allelesFilename)
    return True, results


def upload_new_allele_complete(project_name, sample_id_int, sample_id_ext, raw_path, customer,
                               settings, mydb, log, incomplete_ok=False, use_restricted_db=False,
                               startover=False):
    """adds one new target sequence to TypeLoader
    """
    success, results = handle_new_allele_parsing(project_name, sample_id_int, sample_id_ext,
                                                 raw_path, customer, settings, log,
                                                 use_restricted_db)
    if not success:
        log.warning("Could not upload target file")
        log.warning(results)
        return False, results

    (header_data, filetype, sample_name, targetFamily,
     temp_raw_file, blastXmlFile, fasta_filename, allelesFilename) = results

    if sample_id_int:
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
    if startover:
        if myallele.gene != startover["gene"]:
            return False, f"This used to be a {startover['gene']} allele! " \
                          f"It can only be restarted with another {startover['gene']} allele."

    # save allele files:
    results = save_new_allele(project_name, sample_name, myallele.local_name, ENA_text,
                              filetype, temp_raw_file, blastXmlFile, fasta_filename, False,
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
                                                     ena_path, None, settings, mydb, log,
                                                     startover)
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
    alleles_uploaded = []
    for allele in alleles:
        [nr, sample_id_int, sample_id_ext, raw_path, customer, incomplete_ok] = allele
        log.info("Uploading #{}: {}...".format(nr, sample_id_int))
        success, msg = upload_new_allele_complete(project, sample_id_int, sample_id_ext, raw_path, customer, settings,
                                                  mydb, log, incomplete_ok=incomplete_ok)
        if success:
            local_name = msg
            successful.append("  - #{}: {}".format(nr, local_name))
            alleles_uploaded.append(local_name)
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

    return report, errors_found, alleles_uploaded


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
        EF.make_manifest(file_dic["manifest"], ENA_ID, submission_alias, file_dic["concat_FF_zip"],
                         settings["TL_version"], log)
    except Exception as E:
        log.error("Could not create manifest file!")
        log.exception(E)
        return False, False, "Manifest file problem", "Could not create the manifest file for ENA submission: {}".format(
            repr(E)), []

    ## 3. validate files via CLI
    log.debug("Validating submission files using ENA's Webin-CLI...")
    ena_cmd, msg = EF.make_ENA_CLI_command_string(file_dic["manifest"], file_dic["project_dir"], settings, log)

    if not ena_cmd:
        log.error("Could not generate command for Webin-CLI!")
        return False, False, "Webin-CLI command problem", msg, []

    log.debug("Validating command and files...")

    success, ENA_response, _, problem_samples = EF.handle_webin_CLI(ena_cmd, "validate", submission_alias,
                                                                    file_dic["project_dir"],
                                                                    line_dic, settings, log)
    if not success:
        log.error("Validation by ENA's Webin-CLI failed!")
        log.error(ENA_response)
        return [ENA_response], False, "ENA validation error", ENA_response, problem_samples

    log.debug("\t=> looking good")

    # 3.b) delete the subfolder created by webin CLI before submission, otherwise webinCLI 4.x+ will throw an error
    log.debug("Removing ENA temp dir...")
    ENA_sequence_dir = os.path.join(file_dic["project_dir"], "sequence")
    shutil.rmtree(ENA_sequence_dir)

    ## 4. submit files via CLI
    log.debug("Submitting files...")
    timeout = int(settings["timeout_ena"])
    successful_transmit, ENA_response, analysis_accession_number, problem_samples = EF.handle_webin_CLI(ena_cmd,
                                                                                                        "submit",
                                                                                                        submission_alias,
                                                                                                        file_dic[
                                                                                                            "project_dir"],
                                                                                                        line_dic, settings, log,
                                                                                                        timeout=timeout)
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


def submit_alleles_to_ENA(project_name, ENA_ID, samples, files, settings, log):
    """handles submission of a set of allele files to ENA

    :param project_name: name of the project the alleles belong to
    :param ENA_ID: ENA's internal ID (PRJEB-ID) of the project
    :param samples: list of alleles to submit, format: [[project_name, str(allele_nr)]]
    :param files: list of corresponding ENA files, format: ['project_dir/sample_id_int/allele_name.ena.txt']
    :param settings: the user's settings_dic
    :param log: logger instance
    :return:
            - success (bool)
            - file_dic with affected files, format:
                {'concat_FF_zip': 'project_dir\\PRJEB..._timestamp_flatfile.txt.gz',
                'manifest': 'project_dir\\PRJEB..._timestamp_manifest.txt',
                'project_dir': 'project_dir'}
            - ena_results: tuple with results of processing by ENA's CLI, format:
            ('PRJEB..._timestamp', 'timestamp_sent', 'timestamp_answer', 'ERZ...', 'error_type', 'msg from ENA')
            - problem_samples: list of alleles that did not go through, format [int(allele_nr)]
            - err_type, string of the class of error (if any), for the title of the QMessagebox
            - msg: string with the final message for the user, whether positive or negative
    """
    file_dic, curr_time, analysis_alias = create_ENA_filenames(project_name, ENA_ID, settings, log)

    ena_results, success, err_type, msg, problem_samples = submit_sequences_to_ENA_via_CLI(
        project_name,
        ENA_ID,
        analysis_alias,
        curr_time,
        samples,
        files,
        file_dic,
        settings,
        log)

    try:
        webin_file = os.path.join(file_dic["project_dir"], "webin-cli.report")
        new_path = os.path.join(file_dic["project_dir"], f"{analysis_alias}_webin-cli.report")
        os.rename(webin_file, new_path)
    except IOError:
        log.debug("No webin-cli.report file found")

    return success, file_dic, ena_results, problem_samples, err_type, msg


def upload_allele_with_restricted_db(project_name, sample_id_int, sample_id_ext, raw_path,
                                     customer, reference_alleles,
                                     settings, mydb, log):
    """re-attempts upload of a target allele file, using a restricted reference database.
    This can become necessary if TL cannot automatically find a goo reference allele. (#149)

    :param project_name: name of the project where the target allele should go
    :param sample_id_int: internal sample ID for the target allele
    :param sample_id_ext: external sample ID for the target allele
    :param raw_path: path where the file to be uploaded is located
    :param customer: customer of the target allele (optional field)
    :param reference_alleles: list of reference alleles to use in the restricted database
    :param settings: the current user's settings (dictionary)
    :param mydb: db connection the the user's TL database
    :param log: logger
    :return: success (bool), msg (allele_name if successfull, else error message)
    """
    from typeloader_core import update_reference
    ref_path_orig = os.path.join(settings["root_path"], settings["general_dir"],
                                 settings["reference_dir"])
    target_dir = os.path.join(settings["temp_dir"], "restricted_db")
    success, restricted_db = update_reference.make_restricted_db("restricted", ref_path_orig,
                                                                 reference_alleles, target_dir,
                                                                 settings["blast_path"], log)
    if not success:
        msg = "Creating restricted database did not work! Aborting..."
        log.error(msg)
        return False, "Error while trying to create restricted reference database", msg

    success, msg = upload_new_allele_complete(project_name, sample_id_int,
                                              sample_id_ext, raw_path, customer,
                                              settings, mydb, log,
                                              use_restricted_db=restricted_db)
    return success, msg


def collect_old_files_for_renaming(project_name, sample_id_int, allele_nr, parent, settings, log):
    log.debug("\tFinding old files in database...")
    file_query = f"""select alleles.local_name, raw_file, fasta, blast_xml, ena_file, 
                        ipd_submission_file, ipd_submission_nr
                    from files join alleles on files.local_name = alleles.local_name
                    where alleles.allele_nr = {allele_nr} and files.project = '{project_name}'
                        and files.sample_id_int = '{sample_id_int}'"""
    success, data = db_internal.execute_query(file_query, 7, log,
                                              "retrieving previously created files from database",
                                              parent=parent)
    if not success:
        return False, data, []  # data = err_msg

    if not data:
        return False, "Could not find data for this allele in the database!", []

    if len(data) > 1:
        return False, "Found multiple alleles with this specification! (This should not happen!)", []

    log.info("\tRenaming old files...")
    [local_name, raw_file, fasta, blast_xml, ena_file, ipd_submission_file, ipd_submission_nr] = data[0]
    sample_dir = os.path.join(settings["projects_dir"], project_name, sample_id_int)
    timestamp = general.timestamp("%Y%m%d%H%M%S")

    if ipd_submission_nr and not ipd_submission_file:  # in older samples, the IPD filename was not stored
        for file in [f"{ipd_submission_nr}.txt",
                     f"{ipd_submission_nr}_confirmed.txt"]:
            if os.path.exists(os.path.join(sample_dir, file)):
                ipd_submission_file = file

    files = [raw_file, fasta, blast_xml, ena_file, ipd_submission_file]
    rename_me = []
    for file in files:
        if file:
            split = file.split(".")
            new_file = f"{split[0]}_old_{timestamp}.{'.'.join(split[1:])}"
            rename_me.append((os.path.join(sample_dir, file), os.path.join(sample_dir, new_file)))

    return True, local_name, rename_me


def mark_as_outdated(value):
    """if value exists, mark it with a suffix as outdated
    """
    suffix = "_outdated!"
    if value:
        if value == "None":
            return None
        else:
            return value.replace(suffix, "") + suffix
    return value


def get_protected_values(project_name, sample_id_int, local_name, parent, log):
    log.debug("Getting protected values from db...")

    query = f"""select allele_nr, project_nr, gene, reference_database, database_version, 
                    ena_submission_id, ena_acception_date, ena_accession_nr, 
                    ipd_submission_id, ipd_submission_nr, hws_submission_nr,
                    sample_id_ext, customer, kommentar
                from alleles join samples on alleles.sample_id_int = samples.sample_id_int 
                where local_name = '{local_name}' and project_name = '{project_name}'
                    and alleles.sample_id_int = '{sample_id_int}'
                """

    success, data = db_internal.execute_query(query, 14, log,
                                              "retrieving protected values from database",
                                              parent=parent)
    if not success:
        return False, data
    if not data:
        return False, f"Could not find allele data of allele {local_name}!"
    if len(data) > 1:
        return False, f"Found multiple alleles with this specification! (This should not happen!)"

    [allele_nr, project_nr, gene, reference_database, database_version,
     ena_submission_id, ena_acception_date, ena_accession_nr,
     ipd_submission_id, ipd_submission_nr, hws_submission_nr, sample_id_ext, customer,
     kommentar] = data[0]

    notice = "restarted with fresh sequence"
    kommentar = kommentar.replace(f", {notice}", "").replace(notice, "")  # these should not accumulate
    if kommentar:
        kommentar = ", ".join([kommentar, notice])
    else:
        kommentar = notice

    startover_dic = {"allele_nr": allele_nr,
                     "project_nr": project_nr,
                     "local_name": local_name,
                     "gene": gene,
                     "sample_id_int": sample_id_int,
                     "sample_id_ext": sample_id_ext,
                     "customer": customer,
                     "ena_submission_id": ena_submission_id,
                     "ena_acception_date": mark_as_outdated(ena_acception_date),
                     "ena_accession_nr": mark_as_outdated(ena_accession_nr),
                     "ipd_submission_id": ipd_submission_id,
                     "ipd_submission_nr": mark_as_outdated(ipd_submission_nr),
                     "hws_submission_nr": mark_as_outdated(hws_submission_nr),
                     "ref_db": reference_database,
                     "db_version": database_version,
                     "kommentar": kommentar,
                     "submitted_last": None
                     }

    for key in startover_dic:
        if startover_dic[key] == "None":
            startover_dic[key] = None

    if ipd_submission_id:
        startover_dic["submitted_last"] = "IPD"
    elif ena_submission_id:
        startover_dic["submitted_last"] = "ENA"

    return True, startover_dic


def initiate_startover_allele(project_name, sample_id_int, allele_nr, parent, settings, log):
    log.info(f"Initiating startover...")

    success, err_msg, rename_files = collect_old_files_for_renaming(project_name, sample_id_int, allele_nr, parent,
                                                                    settings, log)
    if not success:
        return False, err_msg, None, None

    local_name = err_msg

    success, results = get_protected_values(project_name, sample_id_int, local_name, parent, log)
    if not success:
        return False, results, None  # results = err_msg

    startover_dic = results
    startover_dic["rename_files"] = rename_files
    db_dic = {"IPD-IMGT/HLA": "HLA",
              "IPD-KIR": "KIR"}
    db_short = db_dic[startover_dic["ref_db"]]

    if settings["db_versions"][db_short] != startover_dic["db_version"]:
        msg = f"This allele was originally uploaded to TypeLoader with {startover_dic['ref_db']} version " \
              f"{startover_dic['db_version']}!"
        msg += "\nDo you wish to reset TypeLoader to this, in order to use the same reference?"
        log.info(msg)
        return True, msg, (db_short, startover_dic["db_version"]), startover_dic

    return True, None, None, startover_dic


# ===========================================================
# main:

def main(settings, log, mydb):
    project = "20210426_ADMIN_MIC_191XML"
    sample_id_int = "old"
    sample_id_ext = "Blubb"
    raw_path = r"C:\Daten\local_data\TypeLoader\staging\data_unittest\reject_xml\unsuitable.xml"
    customer = "DKMS"

    upload_new_allele_complete(project, sample_id_int, sample_id_ext, raw_path, customer,
                               settings, mydb, log)


if __name__ == "__main__":
    from typeloader_GUI import create_connection, close_connection
    import GUI_login

    log = general.start_log(level="debug")
    log.info("<Start {}>".format(os.path.basename(__file__)))
    settings_dic = GUI_login.get_settings("admin", log)
    mydb = create_connection(log, settings_dic["db_file"])
    main(settings_dic, log, mydb)
    close_connection(log, mydb)
    log.info("<End>")
