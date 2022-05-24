#!/usr/bin/env python

from itertools import groupby
from xml.dom import minidom
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
import hashlib
from collections import defaultdict
import ftplib
import logging
import os
import shlex
import subprocess
import gzip
import pycurl
import re

FUSION_INTRON_PATTERN = re.compile('/number=\d+/\d+')


def check_fasta_valid(fasta):
    """checks whether the file opened as fasta conforms to basic fasta format
    """
    line1 = next(fasta)
    if not line1.startswith(">"):
        raise ValueError("FASTA files should have a header starting with >")
    if len(line1.strip()) < 2:
        raise ValueError("This input FASTA file has an empty header! Please put something after the '>'!")
    try:
        line2ok = True
        line2 = next(fasta)
        if not line2.strip():
            line2ok = False
        if line2[0].upper() not in ["A", "T", "G", "C", "N"]:
            line2ok = False
    except StopIteration:
        line2ok = False
    if not line2ok:
        raise ValueError("FASTA files must contain a valid nucleotide sequence after the header!")
    fasta.seek(0)


def fasta_generator(fasta_file):
    """reads a fasta file,
    returns the header and sequence of the first entry
    """
    with open(fasta_file) as fasta:
        check_fasta_valid(fasta)
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
        posHash[dr2sAllele] = {"utr": [], "exons": {}, "introns": {}, "pseudoexons": {}}
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
            else:
                print("Should not go in here")

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
            # only for self-created files
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
        data = [("SUBMISSION",
                 (c.FORM_FILE, submission_xml)),
                ("{}".format(filetype),
                 (c.FORM_FILE, type_xml))]
        c.setopt(c.HTTPPOST, data)
        c.setopt(pycurl.PROXY, proxy)
        c.setopt(pycurl.SSL_VERIFYPEER,
                 0)  # FIXME: (future) use certificates! https://stackoverflow.com/questions/8332643/pycurl-and-ssl-cert
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
    search_alias = subprocess.Popen(shlex.split('find ' + search_dir + ' -type f -name \'*_output.xml\' '),
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    search_alias_pipe1 = subprocess.Popen(shlex.split('xargs grep -H ' + search_string), stdin=search_alias.stdout,
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    search_alias_pipe2 = subprocess.Popen(shlex.split('awk {\'print $4\'} '), stdin=search_alias_pipe1.stdout,
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    search_alias_pipe3 = subprocess.Popen(shlex.split('cut -d \\" -f2'), stdin=search_alias_pipe2.stdout,
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    search_out, search_error = search_alias_pipe3.communicate()
    title = ""
    description = ""
    if (search_out != ""):
        study_xml = search_dir + search_out.strip() + ".xml"
        title, description = parse_study_xml(study_xml)
    else:
        write_log(err_file, "ERROR",
                  " You choose a directory, whose accession number isn't in a study xml file: " + search_string)
        search_out = "[ There is no valid accession number, please do no further progression ]"
    return (search_out.strip(), title, description)


def parse_register_EMBL_xml(filename, filetype, samples=None):
    with open(filename, "r") as f:
        xml_data = f.read()
    problem_samples = []
    try:
        curr_xml = minidom.parseString(xml_data)
        successful = curr_xml.getElementsByTagName('RECEIPT')[0].attributes['success'].value
        if (successful == "true"):
            accession_number = curr_xml.getElementsByTagName(filetype)[0].attributes['accession'].value
        else:
            accession_number = ""
        info = curr_xml.getElementsByTagName('INFO')
        error = curr_xml.getElementsByTagName('ERROR')
        pattern = "Sequence [0-9]+"
        if error:
            successful = False
            errors = []
            if "NodeList" in str(type(error)):
                for i in range(len(error)):
                    mytext = error[i].toprettyxml(encoding="UTF8").decode("UTF8").replace("&quot;", '"').replace(
                        "</ERROR>", "").replace("<ERROR>", "")
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
        info = ""
        if "ExpatError" in str(type(E)):
            try:
                parse_dic = {}
                for element in xml_data[1:-1].split(","):
                    [key, value] = element.replace('"', '').split(":")
                    parse_dic[key] = value

                parseable_reply = True
                info = ""
                for key in ["error", "message", "status"]:
                    if key not in parse_dic:
                        parseable_reply = False
            except:
                parseable_reply = False
            if not parseable_reply:
                try:
                    error = xml_data.split("<body>")[1].split("</body>")[0]
                except IndexError:
                    error = str(xml_data)
                error += "\n\nI cannot parse this, but apparently there's a problem."
                error += "\nCheck EMBL server connection?"
            else:
                error = parse_dic["error"]
                info = parse_dic["message"]
                status = parse_dic["status"]
                if error == "Not Found" and info == "Not Found" and status == 404:
                    error = "Could not reach ENA server! Please check EMBL server connection!"
                    info = "known error"
        else:
            error = "Cannot understand ENA's reply"
        successful = False
        accession_number = ""
    return (successful, accession_number, info, error, problem_samples)


def parse_study_xml(xml_data):
    title = ""
    description = ""
    curr_xml = minidom.parse(xml_data)
    title_element = curr_xml.getElementsByTagName('TITLE')[0]
    if (len(title_element.childNodes) > 0): title = title_element.childNodes[0].data
    desc_element = curr_xml.getElementsByTagName('DESCRIPTION')[0]
    if (len(desc_element.childNodes) > 0):
        description = desc_element.childNodes[0].data
    return (title, description)


def connect_ftp(command, file, username, password, ftp_server, log, modus):
    log.info("Initiating FTP connection...")
    filename = os.path.basename(file)
    try:
        ftp = ftplib.FTP(ftp_server)
        ftp.login(user=username, passwd=password)
        if modus in ["debugging", "testing", "staging"]:
            ftp.debug(2)
        if (command == "delete"):
            ftp.delete(filename)
            log.info("\tsuccessful FTP deletion: " + file)
        if (command == "push"):
            open_file = open(file, 'rb')
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


def adjust_flatfile_before_submission(line, log):
    """looks for fusion intron annotations (which arise around deleted exons, see #194)
    and replaces them with the number of the first involved intron only
    to concur with new ENA annotation requirements of webin CLI 4.X+.
    Also removes the "CC   (file created with TypeLoader Version X)" line.

    All of this only affects the concatenated flatfile, not the individual .ena.txt files.
    """
    if line.startswith("FT        "):
        match = re.search(FUSION_INTRON_PATTERN, line)
        if match:
            matching = match.group()
            replacement = f'/{matching.split("/")[1]}'
            line = line.replace(matching, replacement)
            log.debug("\tReplaced a fusion intron annotation to concur with ENA requirements")
    elif line.startswith("CC   (file created with"):
        line = ""
    return line


def concatenate_flatfile(files, concat_FF_zip, log):
    """concatenates all text files into one gzipped text file;
    returns True if that file has any content, else False
    """
    log.debug("Concatenating {} files...".format(len(files)))
    line_dic = {}  # format: {line number in flatfile : (nr of depicted sequence, local_name of depicted sequence)}
    i = 0  # line number in flatfile
    j = 0  # sequence number in flatfile
    with gzip.open(concat_FF_zip, "wt") as g:
        for file in files:
            sequence = os.path.basename(file).split(".")[0]
            j += 1
            with open(file, "r") as f:
                for line in f:
                    line = adjust_flatfile_before_submission(line, log)
                    i += 1
                    line_dic[i] = (j, sequence)
                    g.write(line)
                g.write("\n")
    log.debug("\t=>Done!")
    if os.path.getsize(concat_FF_zip) > 0:
        return True, line_dic
    else:
        return False, None


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


def make_manifest(manifest_file, ENA_ID, submission_alias, flatfile, TL_version, log):
    with open(manifest_file, "w") as g:
        g.write("STUDY\t{}\n".format(ENA_ID))
        g.write("NAME\t{}\n".format(submission_alias))
        g.write("FLATFILE\t{}\n".format(os.path.basename(flatfile)))
        g.write("SUBMISSION_TOOL\tTypeLoader\n")
        g.write("SUBMISSION_TOOL_VERSION\t{}\n".format(TL_version))
    log.debug("\tmanifest file written to {}".format(manifest_file))


def make_ENA_CLI_command_string(manifest_file, project_dir, settings, log):
    import glob
    # find webin-cli:
    log.debug("Locating ENA's Webin-CLI client...")
    TL_src_dir = os.path.dirname(os.path.dirname(__file__))
    CLI_path = os.path.join(TL_src_dir, "ENA_Webin_CLI")  # should work if executed from Python
    CLI_files = glob.glob(os.path.join(CLI_path, "webin-cli*.jar"))
    if not CLI_files:
        CLI_path2 = os.path.join(os.path.dirname(TL_src_dir), "ENA_Webin_CLI")  # should work if executed from .exe
        CLI_files = glob.glob(os.path.join(CLI_path2, "webin-cli*.jar"))
        if not CLI_files:
            log.error("ENA Webin-CLI not found in {}!".format(CLI_path))
            return False, "ENA Webin-CLI client not found!"

    CLI_file = sorted(CLI_files)[-1]  # if multiple versions found, use highest version
    log.debug("\t=> found: {}".format(CLI_file))

    # create command:
    log.debug("Creating command for Webin-CLI...")
    cmd = ['java', '-jar', CLI_file, '-context', 'sequence', '-manifest', manifest_file,
           '-userName', settings["ftp_user"], '-password', settings["ftp_pwd"], '-centerName',
           '"{}"'.format(settings["xml_center_name"]),
           '-inputDir', project_dir, '-outputDir', project_dir]

    if settings["use_ena_server"] != "PROD":  # use TEST server
        cmd.append("-test")

    log.debug("\t=> done")

    return cmd, None


def parse_ENA_report(report_file, line_dic, log):
    """parses ENA report file generated after rejection by Webin-CLI
    """
    log.info("Reading ENA's reply from {}...".format(report_file))
    problem_samples = []
    msg_dic = defaultdict(list)
    affected_lines_dic = defaultdict(list)

    with open(report_file, "r") as f:
        for line in f:
            log.debug(line.strip())
            try:
                myline = line.split("ERROR: ")[1].split(" [ line: ")
                line_nr = myline[1].split(" ")[0]
                (allele_nr, allele) = line_dic[int(line_nr)]
                if not allele_nr - 1 in problem_samples:
                    problem_samples.append(allele_nr - 1)
                key = "Sequence {} ({})".format(allele_nr, allele)
                if line_nr not in affected_lines_dic[key]:
                    affected_lines_dic[key].append(line_nr)
            except Exception as E:
                log.error("Could not parse ENA response as expected (no standard problem):")
                log.exception(E)
                myline = [line]
                key = "general problem"
            if myline[0] not in msg_dic[key]:  # remove doubled lines
                msg_dic[key].append(myline[0])

    text = ""
    for key in sorted(msg_dic):
        text += " - {}:\n".format(key)
        for line in msg_dic[key]:
            text += line + "\n"
        text += "(Problematic lines in concatenated flatfile: {})\n".format(", ".join(affected_lines_dic[key]))

    return text, problem_samples


def handle_webin_CLI(ena_cmd, modus, submission_alias, project_dir, line_dic, settings, log, timeout=None):
    """calls the command-string via webin-CLI and parses the output
    """
    from subprocess import run, PIPE, CalledProcessError, TimeoutExpired
    success = False
    ENA_submission_ID = None
    problem_samples = []
    report = None

    ena_cmd = ena_cmd + [f"-{modus}"]

    # check whether Java is installed:
    if modus == "validate":
        return_code = os.system("java -version")
        if return_code != 0:
            output_txt = "ERROR: could not find Java on your system!\n\n"
            output_txt += "Please install Java and then restart TypeLoader!"
            return False, output_txt, None, []

    output = None
    proxy = settings["proxy"]

    if proxy:
        log.debug(f"Using proxy {proxy}...")
        s = proxy.split(":")
        if len(s) < 2:
            log.warning("Weird format for proxy! Proxy format should be host:port!")
        else:
            host = s[0]
            port = s[1]

            ena_cmd = [ena_cmd[0]] + \
                      ["-DproxySet=true", f"-Dhttps.proxyHost={host}", f"-Dhttps.proxyPort={port}"] + \
                      ena_cmd[1:]

    try:
        result = run(ena_cmd, stdout=PIPE, stderr=PIPE)#, env=env)
        stderr = result.stderr.decode("utf-8").strip()
        if stderr:
            log.debug("Stderr:")
            log.debug(stderr)

        output = result.stdout.decode("utf-8") + stderr
        result.check_returncode()

    except CalledProcessError as E:
        log.error("ENA's Webin-CLI threw an error after this command:")
        cmd_safe = ['****' if item == settings["ftp_pwd"] else item for item in ena_cmd]
        log.error(cmd_safe)

        log.info("Output:")
        output_txt = E.output.decode("utf-8")
        log.info(output_txt)

    except TimeoutExpired:
        log.error(f"Timeout expired: gave up after {timeout} seconds!")
        output_txt = f"Sorry, could not reach ENA within the given timeout threshold ({timeout} seconds).\n\n"
        output_txt += "Either increase the threshold via Settings => Preferences, or try again later."
        return False, output_txt, None, []

    if not output:
        output = "Webin-CLI generated no output at all! :-(\nSee log file for details."
        output += ""
        log.debug(result)
    output_list = [line.rstrip() for line in output.split("\n") if line]  # make list and remove newlines
    log.debug("Output:")
    log.debug(output)
    if output_list:
        penultimate_line = output_list[-2]
        last_line = output_list[-1]
    else:
        last_line = str(output_list)
        penultimate_line = ""

    s = submission_alias.split("_")
    log.debug("\n".join(output_list))

    if modus == "validate":
        success_txt = 'INFO : The submission has been validated successfully.'
        if penultimate_line == success_txt:
            success = True
            output_txt = penultimate_line.replace("INFO : ", "")
        elif last_line == success_txt:
            success = True
            output_txt = last_line.replace("INFO : ", "")
        else:  # validation failed
            output_txt = "ERROR: ENA rejected your files (validation failed):\n\n"
            report = os.path.join(project_dir, "sequence", submission_alias, "validate",
                                  "{}_{}_flatfile.txt.gz.report".format(s[0], s[1]))

    elif modus == "submit":
        if "The submission has been completed successfully." in last_line \
                or "The TEST submission has been completed successfully." in last_line:
            success = True
            output_txt = "Success!\n\n{}\n{}".format(output_list[-2].replace("INFO : ", ""),
                                                     last_line.replace("INFO : ", ""))
            ENA_submission_ID = last_line.split("was assigned to the submission: ")[1].strip()
        else:
            output_txt = "ERROR: ENA rejected your files (submission failed):\n\n"
            report = os.path.join(project_dir, "sequence", submission_alias, "validate",
                                  "{}_{}_flatfile.txt.gz.report".format(s[0], s[1]))

    if not success:
        log.error("\n".join(output_list))
        if report:
            try:
                report_content, problem_samples = parse_ENA_report(report, line_dic, log)
            except FileNotFoundError:
                error_lines = [line for line in output_list if not line.startswith("INFO")]
                if not error_lines:
                    [line for line in output_list]
                report_content = "\n".join(error_lines) + "\n"
            output_txt += report_content
        else:
            output_txt = "ERROR: ENA rejected your files:\n\n" + "\n".join(output_list)
            output_txt += "\tNo report file was created."

        output_txt += "\nThe complete submission has been rejected."

    else:
        if "-test" in ena_cmd:
            output_txt += "\n\nThis submission is a TEST submission and will be discarded within 24 hours."

    output_txt = output_txt.replace("  ", "\n")  # break weird long lines in ENA-reply

    return success, output_txt, ENA_submission_ID, problem_samples


if __name__ == "__main__":
    log = logging.getLogger()
    manifest_file = r"C:\Daten\local_data\TypeLoader\admin\projects\20211115_ADMIN_HLA-B_NEB1\PRJEB48776_20211116092519_manifest.txt"
    project_dir = r"C:\Daten\local_data\TypeLoader\admin\projects\20211115_ADMIN_HLA-B_NEB1"
    settings = {"ftp_user": "submission@dkms-lab.de",
                "ftp_pwd": "DKMS2805",
                "xml_center_name": "DKMS LIFE SCIENCE LAB",
                "use_ena_server": "TEST"}
    ena_cmd, msg = make_ENA_CLI_command_string(manifest_file, project_dir, settings, log)
    print(ena_cmd)
    line_dic = {1: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 2: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                3: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                4: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 5: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                6: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                7: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 8: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                9: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                10: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 11: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                12: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 13: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                14: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 15: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                16: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 17: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                18: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 19: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                20: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 21: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                22: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 23: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                24: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 25: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                26: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 27: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                28: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 29: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                30: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 31: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                32: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 33: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                34: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 35: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                36: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 37: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                38: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 39: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                40: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 41: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                42: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 43: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                44: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 45: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                46: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 47: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                48: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 49: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                50: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 51: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                52: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 53: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                54: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 55: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                56: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 57: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                58: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 59: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                60: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 61: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                62: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 63: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                64: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 65: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                66: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 67: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                68: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 69: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                70: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 71: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                72: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 73: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                74: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 75: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                76: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 77: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                78: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 79: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                80: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 81: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                82: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 83: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                84: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 85: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                86: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 87: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                88: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 89: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                90: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 91: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                92: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 93: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                94: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 95: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                96: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 97: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                98: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 99: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                100: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 101: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                102: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 103: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                104: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 105: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                106: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 107: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                108: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 109: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                110: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 111: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                112: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 113: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                114: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 115: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                116: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 117: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                118: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 119: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                120: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 121: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                122: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 123: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                124: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 125: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                126: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 127: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                128: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 129: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                130: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 131: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                132: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 133: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                134: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 135: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                136: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 137: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                138: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 139: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                140: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 141: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                142: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 143: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                144: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 145: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                146: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 147: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                148: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 149: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                150: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 151: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                152: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 153: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                154: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 155: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                156: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 157: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                158: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 159: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                160: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 161: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                162: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 163: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                164: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 165: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                166: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 167: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                168: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 169: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                170: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 171: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                172: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 173: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                174: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 175: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                176: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 177: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                178: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 179: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                180: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 181: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                182: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 183: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                184: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 185: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                186: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 187: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                188: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 189: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                190: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 191: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                192: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 193: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                194: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 195: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                196: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 197: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                198: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 199: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                200: (1, 'DKMS-LSL_ID11537498_DPB1_3'), 201: (1, 'DKMS-LSL_ID11537498_DPB1_3'),
                202: (1, 'DKMS-LSL_ID11537498_DPB1_3')}

    modus = "validate"
    submission_alias = "PRJEB48776_20211115090419"

    import shutil
    try:
        shutil.rmtree(os.path.join(project_dir, "sequence"))
    except FileNotFoundError:
        pass

    success, output_txt, ENA_submission_ID, problem_samples = handle_webin_CLI(ena_cmd, modus, submission_alias, project_dir, line_dic, settings, log)
    print(output_txt)
