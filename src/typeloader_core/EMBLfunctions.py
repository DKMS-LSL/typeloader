#!/usr/bin/python

from itertools import groupby
from xml.dom import minidom
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
import hashlib

import configparser as CP
import ftplib
import logging
import os
import shlex
import subprocess
import gzip
import pycurl
import re

def fasta_generator(fasta_file):
    """reads a fasta file,
    returns the header and sequence of the first entry
    """
    with open(fasta_file) as fasta:
        # groupby(data to group, function for grouping)
        tupple_out = (x[1] for x in groupby(fasta, lambda line: line[0] == ">"))
        for header in tupple_out:
            # drop the ">" and takes header
            header = header.__next__()[1:].strip()
            # join all sequence lines to one.
            seq = "".join(s.strip() for s in next(tupple_out))
            yield header, seq

def get_coordinates_from_annotation(annotations):
    posHash = {}
    sequences = {}

    for dr2sAllele in list(annotations.keys()):
        # the number of exon and introns = key of dictionairy, value = positions
        posHash[dr2sAllele] = {"utr":[],"exons":{},"introns":{},"pseudoexons":{}}
        features, coordinates, sequence = annotations[dr2sAllele]["features"], annotations[dr2sAllele]["coordinates"], \
                                                            annotations[dr2sAllele]["sequence"]
        for featureIndex in range(len(features)):
            feature = features[featureIndex]
            if feature == "utr5" or feature == "utr3": 
                posHash[dr2sAllele]["utr"].append(coordinates[featureIndex])
            elif feature[1] == "e":
                posHash[dr2sAllele]["exons"][feature[0]] = coordinates[featureIndex]
            elif feature[1] == "epseudo":
                posHash[dr2sAllele]["pseudoexons"][feature[0]] = coordinates[featureIndex]
            elif feature[1] == "i":
                posHash[dr2sAllele]["introns"][feature[0]] = coordinates[featureIndex]
            else: print("Should not go in here")

        sequences[dr2sAllele] = sequence

    return (posHash, sequences)

def write_log(file, level, text):
    logging.basicConfig(filename=file, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
    if level == "INFO":
        logging.info(text)
    elif level == "DEBUG":
        logging.debug(text)
    elif level == "WARNING":
        logging.warning(text)
    elif level == "ERROR":
        logging.error(text)
    elif level == "CRITICAL":
        logging.critical(text)
    return None

## write an XML
def write_file(data_string, path, log, pretty=True):
    try:
        file_helper = open(path, 'w')
        if (os.path.splitext(path)[1] == ".xml" and pretty):
            #only for self-created files
            pretty_string = prettify(data_string)
            file_helper.write(pretty_string)
        else:
            file_helper.write(data_string)
    except IOError:
        log.error("Can't write" + path + " to disk")
        return False
    else:
        file_helper.close()
        log.info("Wrote " + path + " to disk")
        return True

def submit_project_ENA(submission_xml, type_xml, filetype, embl_server, proxy, output_filename, userpwd):
    with open(output_filename, "wb") as g:
        c = pycurl.Curl()
        c.setopt(c.URL, embl_server)
        c.setopt(c.POST, 1)
        data = [("SUBMISSION", (c.FORM_FILE, submission_xml)),
                ("{}".format(filetype), (c.FORM_FILE, type_xml))]
        c.setopt(c.HTTPPOST, data)
        c.setopt(pycurl.PROXY, proxy)
        c.setopt(pycurl.SSL_VERIFYPEER, 0) #FIXME: (future) use certificates! https://stackoverflow.com/questions/8332643/pycurl-and-ssl-cert   
        c.setopt(pycurl.SSL_VERIFYHOST, 0)
        c.setopt(pycurl.USERPWD, userpwd)
        c.setopt(c.WRITEFUNCTION, g.write)
        try:
            c.perform()
            err = None
        except Exception as E:
            err = E
        finally:
            c.close()
        
    return err

## create a readable XML
def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, "unicode")
    reparsed = minidom.parseString(rough_string)
    pretty = reparsed.toprettyxml(indent='\t', encoding='utf-8').decode("utf-8") 
    return pretty

def generate_project_xml(title, description, alias, center_name):
    xml_root = Element('PROJECT_SET')
    xml_project = SubElement(xml_root, 'PROJECT')
    xml_project.set('alias', alias)
    xml_project.set('center_name', center_name)
    xml_title = SubElement(xml_project, 'TITLE')
    xml_title.text = title
    xml_description = SubElement(xml_project, 'DESCRIPTION')
    xml_description.text = description
    xml_submission_project = SubElement(xml_project, 'SUBMISSION_PROJECT')
    xml_sequencing_project = SubElement(xml_submission_project, 'SEQUENCING_PROJECT')
    return xml_root

def generate_submission_project_xml(alias, center_name, project_xml_filename):
    xml_root = Element('SUBMISSION')
    xml_root.set('alias', alias)
    xml_root.set('center_name', center_name)
    xml_actions = SubElement(xml_root, 'ACTIONS')
    xml_action = SubElement(xml_actions, 'ACTION')
    xml_add = SubElement(xml_action, 'ADD')
    xml_add.set('source', os.path.basename(project_xml_filename))
    xml_add.set('schema', 'project')
    return xml_root

def generate_analysis_xml(title, description, alias, accession, center_name, concat_FF_zip, md5_checksum):
    xml_root = Element('ANALYSIS_SET')
    xml_analysis = SubElement(xml_root, 'ANALYSIS')
    xml_analysis.set('alias', alias)
    xml_analysis.set('center_name', center_name)
    xml_title = SubElement(xml_analysis, 'TITLE')
    xml_title.text = title
    xml_description = SubElement(xml_analysis, 'DESCRIPTION')
    xml_description.text = description
    xml_study_ref = SubElement(xml_analysis, 'STUDY_REF')
    xml_study_ref.set('accession', accession)
    xml_study_ref.text = " "
    xml_analysis_type = SubElement(xml_analysis, 'ANALYSIS_TYPE')
    xml_sequence_flatfile = SubElement(xml_analysis_type, 'SEQUENCE_FLATFILE')
    xml_files = SubElement(xml_analysis, 'FILES')
    xml_file = SubElement(xml_files, 'FILE')
    xml_file.set('checksum', md5_checksum)
    xml_file.set('checksum_method', 'MD5')
    xml_file.set('filename', os.path.basename(concat_FF_zip))
    xml_file.set('filetype', 'flatfile')
    return xml_root

def generate_submission_ff_xml(alias, center_name, analysis_xml_filename):
    xml_root = Element('SUBMISSION')
    xml_root.set('alias', alias)
    xml_root.set('center_name', center_name)
    xml_actions = SubElement(xml_root, 'ACTIONS')
    xml_action = SubElement(xml_actions, 'ACTION')
    xml_add = SubElement(xml_action, 'ADD')
    xml_add.set('source', analysis_xml_filename)
    xml_add.set('schema', 'analysis')
    return xml_root

def get_study_info(search_dir, search_string, err_file):
    ## extract alias for seaching study information
    search_alias = subprocess.Popen(shlex.split('find ' + search_dir + ' -type f -name \'*_output.xml\' '), stdout = subprocess.PIPE, stderr=subprocess.PIPE)
    search_alias_pipe1 = subprocess.Popen(shlex.split('xargs grep -H ' + search_string), stdin=search_alias.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    search_alias_pipe2 = subprocess.Popen(shlex.split('awk {\'print $4\'} '), stdin=search_alias_pipe1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    search_alias_pipe3 = subprocess.Popen(shlex.split('cut -d \\" -f2'), stdin=search_alias_pipe2.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    search_out, search_error = search_alias_pipe3.communicate()
    title = ""
    description = ""
    if (search_out != ""):
        study_xml = search_dir + search_out.strip() + ".xml"
        title, description = parse_study_xml(study_xml)
    else:
        write_log(err_file, "ERROR", " You choose a directory, whose accession number isn't in a study xml file: " + search_string)
        search_out = "[ There is no valid accession number, please do no further progression ]"
    return (search_out.strip(), title, description)

def parse_register_EMBL_xml(filename, filetype, samples = None):
    with open(filename, "r") as f:
        xml_data = f.read()
    try:
        curr_xml = minidom.parseString(xml_data)
        successful = curr_xml.getElementsByTagName('RECEIPT')[0].attributes['success'].value
        if (successful == "true"):
            accession_number = curr_xml.getElementsByTagName(filetype)[0].attributes['accession'].value
        else:
            accession_number = ""
        info = curr_xml.getElementsByTagName('INFO')
        error = curr_xml.getElementsByTagName('ERROR')
        problem_samples = []
        pattern = "Sequence [0-9]+"
        if error:
            successful = False
            errors = []
            if "NodeList" in str(type(error)):
                for i in range(len(error)):
                    mytext = error[i].toprettyxml(encoding="UTF8").decode("UTF8").replace("&quot;",'"').replace("</ERROR>","").replace("<ERROR>","")
                    if mytext:
                        splitted = mytext.split('filetype:"flatfile". ')
                        if len(splitted) == 2:
                            info = "known error"
                            mytext = splitted[1]
                            match = re.search(pattern, mytext)
                            if match:
                                try:
                                    found = match.group()
                                    nr = int(found.split()[1])
                                    problem_samples.append(nr - 1)
                                    [_, _, _, local_name] = samples[nr - 1]
                                    mytext = mytext.replace(found, "{} ({})".format(found, local_name))
                                    
                                except Exception as E:
                                    errors.append(repr(E))
                            errors.append(mytext)
                        else:
                            errors.append(mytext)
            error = "".join(errors)
    except Exception as E:
        if "ExpatError" in str(type(E)):
            parse_dic = {}
            for element in xml_data[1:-1].split(","):
                [key, value] = element.replace('"','').split(":")
                parse_dic[key] = value
            error = parse_dic["error"]
            info = parse_dic["message"]
            status = parse_dic["status"]
            if error == "Not Found" and info == "Not Found" and status == 404:
                error = "Could not reach ENA server! Please check EMBL server connection!"
                info = "known error"
        else:
            error = E
            info = ""
        successful = False
        accession_number = ""
    return (successful, accession_number, info, error, problem_samples)

def parse_study_xml(xml_data):
    title = ""
    description = ""
    curr_xml = minidom.parse(xml_data)
    title_element = curr_xml.getElementsByTagName('TITLE')[0]
    if (len(title_element.childNodes) > 0): title = title_element.childNodes[0].data
    desc_element =  curr_xml.getElementsByTagName('DESCRIPTION')[0]
    if (len(desc_element.childNodes) > 0):
        description = desc_element.childNodes[0].data
    return (title, description)

def connect_ftp(command, file, username, password, ftp_server, log, modus):
    log.info("Initiating FTP connection...")
    filename = os.path.basename(file)
    try:
        ftp = ftplib.FTP(ftp_server)
        ftp.login(user = username, passwd = password)
        if modus in ["debugging", "testing", "staging"]:
            ftp.debug(2)
        if (command == "delete"):
            ftp.delete(filename)
            log.info("\tsuccessful FTP deletion: " + file)
        if (command == "push"):
            open_file = open(file,'rb')
            ftp.storbinary('STOR ' + filename, open_file)
            open_file.close()
            log.info("\tsuccessful FTP push: " + file)
        ftp.quit()
        return_string = "True"
    except ftplib.all_errors as e:
        log.debug(",".join([username, password, ftp_server]))
        return_string = repr(e)
        log.exception(e)
        log.error("FTP error: " + repr(e))
    except Exception as E:
        log.debug(",".join([username, password, ftp_server]))
        return_string = repr(E)
        log.exception(E)
        log.error("Problem with FTP connection!")
    return (return_string)


def concatenate_flatfile(files, concat_FF_zip, log):
    """concatenates all text files into one gzipped text file;
    returns True if that file has any content, else False
    """
    log.info("Concatenating {} files...".format(len(files)))
    with gzip.open(concat_FF_zip, "wt") as g:
        for file in files:
            with open(file, "r") as f:
                for line in f:
                    g.write(line)
                g.write("\n")
    log.info("\t=>Done!")
    if os.path.getsize(concat_FF_zip) > 0:
        return True
    else:
        return False
    
def make_md5(concat_FF, log):
    with open(concat_FF, 'rb') as fh:
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        checksum = m.hexdigest()
        log.info("Checksum of file {} is {}".format(concat_FF, checksum))
        return checksum


